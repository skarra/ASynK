##
## Created : Sun May 25 09:00:00 PDT 2026
## SPDX-FileCopyrightText: 2014-2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
## ####
##
## Microsoft Graph API client for Exchange Online contact sync.
## Replaces the legacy pyews EWS/SOAP client.
##

import json, logging, os, time

import msal
import requests

GRAPH_BASE_URL = 'https://graph.microsoft.com/v1.0'
GRAPH_SCOPES   = ['Contacts.ReadWrite', 'User.Read']
DEFAULT_PAGE_SIZE = 250

class GraphAPIError(Exception):
    """Raised when a Graph API request fails."""

    def __init__ (self, status_code, error_code=None, message=None):
        self.status_code = status_code
        self.error_code  = error_code
        self.message     = message
        super().__init__(
            'Graph API Error %d: [%s] %s' % (status_code,
                                              error_code or 'unknown',
                                              message or ''))

class GraphAuthError(Exception):
    """Raised when authentication fails."""
    pass


class DeltaSyncResult:
    """Container for the results of a delta sync query."""

    def __init__ (self, changed, deleted, delta_link):
        self.changed    = changed       # list of contact dicts (new + modified)
        self.deleted    = deleted        # list of contact ID strings
        self.delta_link = delta_link     # URL string for next delta query


class GraphAuthProvider:
    """Handles OAuth 2.0 authentication for Microsoft Graph using MSAL.

    Uses the device code flow which is suitable for CLI applications.
    Tokens are cached to disk so that subsequent runs do not require
    re-authentication.
    """

    def __init__ (self, client_id, tenant_id='common',
                  token_cache_path=None):
        self.client_id  = client_id
        self.tenant_id  = tenant_id
        self.authority   = 'https://login.microsoftonline.com/%s' % tenant_id

        if token_cache_path is None:
            asynk_dir = os.path.expanduser('~/.asynk')
            token_cache_path = os.path.join(asynk_dir,
                                            'graph_token_cache.json')

        self.token_cache_path = token_cache_path
        self.cache = self._load_cache()

        self.app = msal.PublicClientApplication(
            self.client_id,
            authority=self.authority,
            token_cache=self.cache)

        self._access_token = None

    ## ----------------------------------------------------------------
    ## Public API
    ## ----------------------------------------------------------------

    def authenticate (self):
        """Acquire an access token, using the cache if possible.

        On first run (or when the cached token has expired and cannot be
        refreshed), the device code flow is initiated: the user is asked
        to visit a URL and enter a code.

        Returns the access token string.
        """

        ## 1. Try silent acquisition from cache
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(GRAPH_SCOPES,
                                                   account=accounts[0])
            if result and 'access_token' in result:
                self._access_token = result['access_token']
                self._save_cache()
                logging.debug('Graph API: acquired token silently from cache')
                return self._access_token

        ## 2. Fall back to device code flow
        flow = self.app.initiate_device_flow(scopes=GRAPH_SCOPES)
        if 'user_code' not in flow:
            raise GraphAuthError(
                'Could not initiate device code flow: %s' %
                flow.get('error_description', 'unknown error'))

        print()
        print('=== Microsoft Graph Authentication ===')
        print('To sign in, visit: %s' % flow['verification_uri'])
        print('and enter the code: %s' % flow['user_code'])
        print()

        result = self.app.acquire_token_by_device_flow(flow)
        if 'access_token' not in result:
            raise GraphAuthError(
                'Authentication failed: %s' %
                result.get('error_description', 'unknown error'))

        self._access_token = result['access_token']
        self._save_cache()
        logging.info('Graph API: authentication successful')
        return self._access_token

    def get_headers (self):
        """Return HTTP headers with a valid Bearer token."""

        if self._access_token is None:
            self.authenticate()

        return {
            'Authorization'  : 'Bearer %s' % self._access_token,
            'Content-Type'   : 'application/json',
        }

    ## ----------------------------------------------------------------
    ## Internal helpers
    ## ----------------------------------------------------------------

    def _load_cache (self):
        cache = msal.SerializableTokenCache()
        if os.path.isfile(self.token_cache_path):
            try:
                with open(self.token_cache_path, 'r') as f:
                    cache.deserialize(f.read())
                logging.debug('Loaded token cache from %s',
                              self.token_cache_path)
            except Exception as e:
                logging.warning('Could not load token cache: %s', e)

        return cache

    def _save_cache (self):
        if self.cache.has_state_changed:
            cache_dir = os.path.dirname(self.token_cache_path)
            if cache_dir and not os.path.isdir(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)

            with open(self.token_cache_path, 'w') as f:
                f.write(self.cache.serialize())
            logging.debug('Saved token cache to %s', self.token_cache_path)


class GraphContactsClient:
    """REST client for Microsoft Graph v1.0 Contacts API.

    Provides methods for CRUD operations on contacts and contact folders,
    delta sync queries, open extension management, and JSON batching.
    """

    MAX_BATCH_SIZE  = 20      # Graph API batch limit
    MAX_RETRIES     = 3
    RETRY_BACKOFF   = 1.0     # seconds, doubled on each retry

    def __init__ (self, auth_provider):
        self.auth = auth_provider
        self.session = requests.Session()

    ## ================================================================
    ## Contact Folder operations
    ## ================================================================

    def list_contact_folders (self):
        """Return a list of all contact folder dicts."""

        return list(self._paginate('/me/contactFolders'))

    def create_contact_folder (self, display_name):
        """Create a new contact folder and return the folder dict."""

        body = {'displayName': display_name}
        return self._request('POST', '/me/contactFolders', json=body)

    def delete_contact_folder (self, folder_id):
        """Delete a contact folder by ID."""

        self._request('DELETE', '/me/contactFolders/%s' % folder_id)

    ## ================================================================
    ## Contact CRUD operations
    ## ================================================================

    def list_contacts (self, folder_id=None, select=None, expand=None):
        """Return a list of all contacts in the specified folder (or default
        contacts folder if folder_id is None). Handles pagination."""

        if folder_id:
            path = '/me/contactFolders/%s/contacts' % folder_id
        else:
            path = '/me/contacts'

        params = {'$top': str(DEFAULT_PAGE_SIZE)}
        if select:
            params['$select'] = select
        if expand:
            params['$expand'] = expand
        else:
            params['$expand'] = 'extensions'

        return list(self._paginate(path, params=params))

    def get_contact (self, contact_id, select=None, expand=None):
        """Fetch a single contact by ID."""

        params = {}
        if select:
            params['$select'] = select
        if expand:
            params['$expand'] = expand
        else:
            params['$expand'] = 'extensions'

        return self._request('GET', '/me/contacts/%s' % contact_id,
                             params=params or None)

    def get_contacts (self, contact_ids, select=None, expand=None):
        """Fetch multiple contacts by IDs using batching."""

        if not contact_ids:
            return []

        params_str = ''
        if expand:
            params_str += '?$expand=%s' % expand
        elif expand is None:
            params_str += '?$expand=extensions'
        if select:
            sep = '&' if params_str else '?'
            params_str += '%s$select=%s' % (sep, select)

        batch_reqs = []
        for i, cid in enumerate(contact_ids):
            batch_reqs.append({
                'id'     : str(i),
                'method' : 'GET',
                'url'    : '/me/contacts/%s%s' % (cid, params_str),
            })

        responses = self._batch(batch_reqs)

        ## Collect successful responses in order
        result_map = {}
        for resp in responses:
            rid = resp.get('id')
            status = resp.get('status', 0)
            if 200 <= status < 300:
                result_map[rid] = resp.get('body', {})
            else:
                logging.warning('Batch GET contact failed for request %s: '
                                'status=%d', rid, status)

        return [result_map[str(i)] for i in range(len(contact_ids))
                if str(i) in result_map]

    def create_contact (self, folder_id, contact_dict):
        """Create a single contact in the specified folder."""

        if folder_id:
            path = '/me/contactFolders/%s/contacts' % folder_id
        else:
            path = '/me/contacts'

        return self._request('POST', path, json=contact_dict)

    def create_contacts (self, folder_id, contact_dicts):
        """Batch create contacts. Returns list of created contact dicts."""

        if not contact_dicts:
            return []

        if folder_id:
            path = '/me/contactFolders/%s/contacts' % folder_id
        else:
            path = '/me/contacts'

        batch_reqs = []
        for i, cd in enumerate(contact_dicts):
            batch_reqs.append({
                'id'      : str(i),
                'method'  : 'POST',
                'url'     : path,
                'body'    : cd,
                'headers' : {'Content-Type': 'application/json'},
            })

        responses = self._batch(batch_reqs)
        results = []
        for resp in responses:
            status = resp.get('status', 0)
            if 200 <= status < 300:
                results.append(resp.get('body', {}))
            else:
                err = resp.get('body', {}).get('error', {})
                logging.error('Batch create failed (status %d): %s',
                              status, err.get('message', 'unknown'))
                results.append(None)

        return results

    def update_contact (self, contact_id, patch_dict):
        """Update a single contact with a partial JSON patch."""

        return self._request('PATCH', '/me/contacts/%s' % contact_id,
                             json=patch_dict)

    def update_contacts (self, updates):
        """Batch update contacts.

        updates is a list of (contact_id, patch_dict) tuples.
        Returns list of updated contact dicts.
        """

        if not updates:
            return []

        batch_reqs = []
        for i, (cid, patch) in enumerate(updates):
            batch_reqs.append({
                'id'      : str(i),
                'method'  : 'PATCH',
                'url'     : '/me/contacts/%s' % cid,
                'body'    : patch,
                'headers' : {'Content-Type': 'application/json'},
            })

        responses = self._batch(batch_reqs)
        results = []
        for resp in responses:
            status = resp.get('status', 0)
            if 200 <= status < 300:
                results.append(resp.get('body', {}))
            else:
                err = resp.get('body', {}).get('error', {})
                logging.error('Batch update failed (status %d): %s',
                              status, err.get('message', 'unknown'))
                results.append(None)

        return results

    def delete_contact (self, contact_id):
        """Delete a single contact."""

        self._request('DELETE', '/me/contacts/%s' % contact_id)

    def delete_contacts (self, contact_ids):
        """Batch delete contacts."""

        if not contact_ids:
            return

        batch_reqs = []
        for i, cid in enumerate(contact_ids):
            batch_reqs.append({
                'id'     : str(i),
                'method' : 'DELETE',
                'url'    : '/me/contacts/%s' % cid,
            })

        responses = self._batch(batch_reqs)
        for resp in responses:
            status = resp.get('status', 0)
            if status >= 300:
                err = resp.get('body', {}).get('error', {})
                logging.error('Batch delete failed for request %s '
                              '(status %d): %s',
                              resp.get('id'), status,
                              err.get('message', 'unknown'))

    ## ================================================================
    ## Delta Sync
    ## ================================================================

    def delta_sync (self, folder_id, delta_link=None):
        """Perform a delta sync for contacts in the specified folder.

        On the first call, pass delta_link=None to get all contacts.
        On subsequent calls, pass the delta_link from the previous result
        to get only changes.

        Returns a DeltaSyncResult with changed contacts, deleted IDs,
        and the new delta_link to persist.
        """

        if delta_link:
            ## Use the saved delta link directly (it's a full URL)
            url = delta_link
        else:
            url = '%s/me/contactFolders/%s/contacts/delta' % (
                GRAPH_BASE_URL, folder_id)

        changed = []
        deleted = []

        while url:
            resp = self.session.get(url, headers=self.auth.get_headers())
            self._check_response(resp)
            data = resp.json()

            for item in data.get('value', []):
                if '@removed' in item:
                    deleted.append(item['id'])
                else:
                    changed.append(item)

            ## Follow @odata.nextLink for pagination, or save deltaLink
            url = data.get('@odata.nextLink')
            if not url:
                new_delta_link = data.get('@odata.deltaLink')

        return DeltaSyncResult(changed=changed, deleted=deleted,
                               delta_link=new_delta_link)

    ## ================================================================
    ## Open Extensions
    ## ================================================================

    def get_extension (self, contact_id, extension_name):
        """Fetch an open extension from a contact. Returns the extension
        dict, or None if not found."""

        path = '/me/contacts/%s/extensions/%s' % (contact_id,
                                                   extension_name)
        try:
            return self._request('GET', path)
        except GraphAPIError as e:
            if e.status_code == 404:
                return None
            raise

    def set_extension (self, contact_id, extension_name, data):
        """Create or update an open extension on a contact.

        data should be a dict of key-value pairs to store.
        """

        ext_body = dict(data)
        ext_body['@odata.type'] = 'microsoft.graph.openTypeExtension'
        ext_body['extensionName'] = extension_name

        ## Try PATCH first (update existing)
        path = '/me/contacts/%s/extensions/%s' % (contact_id,
                                                   extension_name)
        try:
            return self._request('PATCH', path, json=ext_body)
        except GraphAPIError as e:
            if e.status_code != 404:
                raise

        ## Extension doesn't exist yet; create it
        path = '/me/contacts/%s/extensions' % contact_id
        return self._request('POST', path, json=ext_body)

    ## ================================================================
    ## Internal HTTP helpers
    ## ================================================================

    def _request (self, method, path, json=None, params=None):
        """Execute an HTTP request against the Graph API.

        Handles auth headers, throttling (429), and transient errors
        (503, 504) with exponential backoff.
        """

        url = '%s%s' % (GRAPH_BASE_URL, path) if path.startswith('/') else path
        backoff = self.RETRY_BACKOFF

        for attempt in range(self.MAX_RETRIES + 1):
            headers = self.auth.get_headers()
            resp = self.session.request(method, url, headers=headers,
                                        json=json, params=params)

            if resp.status_code == 429:
                retry_after = int(resp.headers.get('Retry-After', 5))
                logging.warning('Graph API throttled (429). Retrying '
                                'after %d seconds...', retry_after)
                time.sleep(retry_after)
                continue

            if resp.status_code in (503, 504) and attempt < self.MAX_RETRIES:
                logging.warning('Graph API transient error (%d). Retrying '
                                'in %.1f seconds...', resp.status_code,
                                backoff)
                time.sleep(backoff)
                backoff *= 2
                continue

            break

        self._check_response(resp)

        ## DELETE returns 204 No Content
        if resp.status_code == 204:
            return None

        return resp.json()

    def _check_response (self, resp):
        """Raise GraphAPIError if the response indicates failure."""

        if resp.status_code >= 400:
            try:
                body = resp.json()
                error = body.get('error', {})
                raise GraphAPIError(
                    status_code=resp.status_code,
                    error_code=error.get('code'),
                    message=error.get('message'))
            except (ValueError, KeyError):
                raise GraphAPIError(
                    status_code=resp.status_code,
                    message=resp.text)

    def _paginate (self, path, params=None):
        """Generator that yields individual items from a paginated
        Graph API collection endpoint."""

        url = '%s%s' % (GRAPH_BASE_URL, path)
        if params is None:
            params = {'$top': str(DEFAULT_PAGE_SIZE)}

        while url:
            resp = self.session.get(url, headers=self.auth.get_headers(),
                                    params=params)
            self._check_response(resp)
            data = resp.json()

            for item in data.get('value', []):
                yield item

            ## On subsequent pages, the full URL is in @odata.nextLink
            ## and we should NOT pass params again (they're in the URL)
            url = data.get('@odata.nextLink')
            params = None

    def _batch (self, requests_list):
        """Execute Graph API JSON batch requests.

        Automatically chunks into groups of MAX_BATCH_SIZE (20).
        Returns a flat list of response objects.
        """

        all_responses = []

        for i in range(0, len(requests_list), self.MAX_BATCH_SIZE):
            chunk = requests_list[i:i + self.MAX_BATCH_SIZE]

            batch_body = {'requests': chunk}
            resp = self._request('POST', '/$batch', json=batch_body)

            if resp and 'responses' in resp:
                all_responses.extend(resp['responses'])
            else:
                logging.error('Batch request returned unexpected response')

        return all_responses
