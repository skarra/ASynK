##
## Created : Mon Mar 31 15:48:05 IST 2014
## SPDX-FileCopyrightText: 2014-2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
## ####
##
## This is an implementation of the MS Exchange PIMDB by extending the PIMDB
## abstract base class.
##
## Rewritten for Microsoft Graph API, replacing the legacy pyews EWS client.
##

import logging, os

from folder    import Folder
from folder_ex import EXContactsFolder
from pimdb     import PIMDB

from msgraph_client import GraphAuthProvider, GraphContactsClient

class EXPIMDB(PIMDB):

    def __init__ (self, config, client_id=None, tenant_id=None,
                  token_cache_path=None, username=None):
        """Initialize the Exchange PIMDB with Graph API authentication.

        Authentication uses OAuth 2.0 device code flow (suitable for CLI
        apps). The user will be prompted to visit a URL and enter a code
        on the first run; subsequent runs use the cached token silently.

        Args:
            config: ASynK config object
            client_id: Azure AD app registration client ID. If None, read
                       from config (ex.client_id).
            tenant_id: Azure AD tenant ID. Defaults to 'common' (multi-tenant).
            token_cache_path: File path for MSAL token cache persistence.
            username: Exchange username or account label.
        """

        PIMDB.__init__(self, config)

        ## Read Graph API credentials from config or arguments
        dbc = config.get_db_config('ex')

        if client_id is None:
            client_id = dbc.get('client_id') if dbc else None
        if tenant_id is None:
            tenant_id = dbc.get('tenant_id', 'common') if dbc else 'common'

        if username is None:
            username = dbc.get('username') if dbc else None

        if token_cache_path is None:
            token_cache_path = dbc.get('token_cache_path') if dbc else None
            # If still None, but username is provided, derive it:
            if token_cache_path is None and username:
                user_dir = config.get_user_dir()
                token_cache_path = os.path.join(user_dir, f'graph_token_cache_{username}.json')

        if not client_id:
            raise ValueError(
                'Exchange Online requires an Azure AD client_id. '
                'Set it in the config file under ex.client_id or pass it '
                'as a parameter.')

        self.set_client_id(client_id)
        self.set_tenant_id(tenant_id)
        self.set_token_cache_path(token_cache_path)
        self.set_username(username)

        self._graph_init()
        self.set_folders()
        self.set_def_folders()

    ##
    ## First implementation of the abstract methods of PIMDB.
    ##

    def get_dbid (self):
        """See the documentation in class PIMDB"""

        return 'ex'

    def list_folders (self, silent=False):
        """List all contact folders from Exchange Online via Graph API."""

        logging.info('pimdb_ex:list_folders()... Begin')
        graph_folders = self.get_graph_client().list_contact_folders()

        for i, f in enumerate(graph_folders):
            if not silent:
                logging.info(' %2d: Folder Name: %-25s ID: %s',
                             i, f.get('displayName', ''), f.get('id', ''))

        logging.info('pimdb_ex:list_folders()... End')

        return graph_folders

    def new_folder (self, fname, ftype=Folder.CONTACT_t, storeid=None):
        """Create a new folder of specified type and return the folder dict.
        Currently only contact folders are supported via Graph API.

        type has to be one of the Folder.valid_types
        """

        if not ftype in Folder.valid_types:
            logging.error('Cannot create folder of type: %s', ftype)
            return None

        if ftype != Folder.CONTACT_t:
            logging.error('Graph API connector only supports contact folders')
            return None

        try:
            res = self.get_graph_client().create_contact_folder(fname)
        except Exception as e:
            logging.error('Could not create folder (%s): %s', fname, e)
            return None

        return res

    def show_folder (self, gid):
        logging.info('%s: Not Implemented', 'pimdb_ex:show_folder()')

    def del_folder (self, fid):
        try:
            self.get_graph_client().delete_contact_folder(fid)
        except Exception as e:
            logging.error('Could not delete folder (%s): %s', fid, e)

    def set_folders (self):
        """See the documentation in class PIMDB"""

        ## Fetch all contact folders from Graph API and wrap them as
        ## EXContactsFolder instances
        logging.debug('EXPIMDB.set_folders(): Begin')
        graph_folders = self.list_folders(silent=True)

        for gf in graph_folders:
            f = EXContactsFolder(self, gf)
            self.add_to_folders(f)
            logging.info('Added Exchange folder %s',
                         gf.get('displayName', ''))

        logging.debug('EXPIMDB.set_folders(): End')

    def set_def_folders (self):
        """See the documentation in class PIMDB"""

        cf = self.folders.get('contacts', [])
        if cf:
            self.def_folder['contacts'] = cf[0]

    def set_sync_folders (self):
        """See the documentation in class PIMDB"""

        raise NotImplementedError

    def prep_for_sync (self, dbid, pname, dr):
        pass

    ##
    ## Now the non-abstract methods and internal methods
    ##

    def get_client_id (self):
        return self._get_att('client_id')

    def set_client_id (self, cid):
        return self._set_att('client_id', cid)

    def get_tenant_id (self):
        return self._get_att('tenant_id')

    def set_tenant_id (self, tid):
        return self._set_att('tenant_id', tid)

    def get_token_cache_path (self):
        return self._get_att('token_cache_path')

    def set_token_cache_path (self, path):
        return self._set_att('token_cache_path', path)

    def get_username (self):
        return self._get_att('username')

    def set_username (self, username):
        return self._set_att('username', username)

    def get_graph_client (self):
        return self._get_att('graph_client')

    def set_graph_client (self, gc):
        return self._set_att('graph_client', gc)

    ## Backward compat aliases for code that uses the old EWS interface name
    def get_ews (self):
        return self.get_graph_client()

    def set_ews (self, ews):
        return self.set_graph_client(ews)

    def _graph_init (self):
        """Initialize the Graph API auth provider and client."""

        logging.debug('Initializing Graph API client for Exchange Online...')

        auth = GraphAuthProvider(
            client_id=self.get_client_id(),
            tenant_id=self.get_tenant_id(),
            token_cache_path=self.get_token_cache_path(),
            username=self.get_username())

        auth.authenticate()
        client = GraphContactsClient(auth)
        self.set_graph_client(client)

        ## Expose the authenticated account email so callers (init
        ## wizard, sync verification) can display and persist it.
        self.authenticated_email = getattr(auth, 'authenticated_email', None)

        logging.debug('Graph API client initialized successfully.')

    ## Legacy aliases for backward compatibility
    def get_user (self):
        return self.get_client_id()

    def set_user (self, user):
        return self.set_client_id(user)

    def get_pw (self):
        return None

    def set_pw (self, pw):
        pass

    def get_url (self):
        return 'https://graph.microsoft.com/v1.0'

    def set_url (self, url):
        pass
