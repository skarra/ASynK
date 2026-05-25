##
## Created : Thu Jul 07 14:47:54 IST 2011
## SPDX-FileCopyrightText: 2011-2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
## ####
##
## Google Contacts PIMDB implementation using the People API v1.
## Replaces the old GData/Atom-based implementation.
##

import logging, os, pickle, sys

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from state import Config
from pimdb import PIMDB, GoutInvalidPropValueError
from folder import Folder

from folder_gc import GCContactsFolder

## The People API scope for full contacts access (read/write).
SCOPES = ['https://www.googleapis.com/auth/contacts']

## personFields to request when listing connections. This should cover all
## the fields ASynK cares about.
PERSON_FIELDS = ','.join([
    'names', 'nicknames', 'emailAddresses', 'phoneNumbers', 'addresses',
    'organizations', 'birthdays', 'events', 'urls', 'imClients',
    'biographies', 'memberships', 'userDefined', 'photos', 'genders',
    'metadata',
])

## Fields that can actually be updated in the People API.
UPDATE_PERSON_FIELDS = ','.join([
    'names', 'nicknames', 'emailAddresses', 'phoneNumbers', 'addresses',
    'organizations', 'birthdays', 'events', 'urls', 'imClients',
    'biographies', 'memberships', 'userDefined', 'genders',
])

class GCPIMDB(PIMDB):
    """GC object is a wrapper for Google Contacts via the People API v1."""

    def __init__ (self, config, user, pw):
        """Initialise a Google Contacts PIMDB.

        user: a label used to identify the token file (e.g. email prefix)
        pw:   path to the OAuth2 client secrets JSON file (credentials.json)
        """
        PIMDB.__init__(self, config)
        self.set_user(user)
        self.set_cs(pw)
        self.gc_init()

        self.set_folders()

    ##
    ## First implementation of the abstract methods of PIMDB.
    ##

    def get_dbid (self):
        """See the documentation in class PIMDB"""

        return 'gc'

    def list_folders (self, silent=False):
        """List all contact groups.  Returns a list of
        (resourceName, name, group_resource) tuples."""

        ret = []
        groups = self._list_contact_groups()

        for i, group in enumerate(groups):
            name = group.get('name', '(unnamed)')
            resource_name = group['resourceName']
            if not silent:
                logging.info(' %2d: Contacts Name: %-25s ID: %s',
                             i, name, resource_name)
            ret.append((resource_name, name, group))

        return ret

    def new_folder (self, fname, ftype=None, storeid=None):
        if not ftype:
            ftype = Folder.CONTACT_t

        if ftype != Folder.CONTACT_t:
            logging.error('Only Contact Groups are supported at this time.')
            return None

        body = {'contactGroup': {'name': fname}}
        result = self.get_service().contactGroups().create(body=body).execute()

        if result:
            resource_name = result['resourceName']
            name = result.get('name', fname)
            logging.info('Successfully created group. ID: %s', resource_name)
            f = GCContactsFolder(self, resource_name, name, result)
            self.add_contacts_folder(f)
            return resource_name
        else:
            logging.error('Could not create Group \'%s\'', fname)
            return None

    def show_folder (self, gid):
        """Print a summary of folder details, including a summary of the
        included items - a one line per item"""

        f, ftype = self.find_folder(gid)

        if not f:
            logging.error('Group ID not found in folder list: %s', gid)
            return False

        f.show()
        return True

    def del_folder (self, gid, store=None):
        """Delete the specified folder on the Google server. This will first
        delete all the contained contact entires, and then delete the group
        itself, so no trace remains.

        The 'store' paramter is ignored. It is needed for other PIMDBs only.
        """

        f, ftype = self.find_folder(gid)

        if not f:
            logging.error('Group ID not found in folder list: %s', gid)
            return

        logging.info('Deleting Entries for Group: %s...', f.get_name())
        f.del_all_entries()
        logging.info('Deleting Entries for Group: %s...done', f.get_name())

        logging.info('Deleting the Group from Google\'s servers...')
        self.get_service().contactGroups().delete(
            resourceName=gid).execute()
        logging.info('Deleting the Group from Google\'s servers...done')

        self.remove_folder_from_lists(f, ftype)

    def set_folders (self):
        """See the documentation in class PIMDB"""

        logging.debug('Getting Group List to populate folders...')
        groups = self.list_folders(silent=True)
        for (gid, gn, gcentry) in groups:
            f = GCContactsFolder(self, gid, gn, gcentry)
            self.add_contacts_folder(f)
            logging.debug('Processing Folder: %s...', gn)
            ## The system group for "My Contacts" in People API is
            ## "contactGroups/myContacts"
            if gid == 'contactGroups/myContacts':
                self.set_def_folder(Folder.CONTACT_t, f)

    def set_def_folders (self):
        """See the documentation in class PIMDB"""

        ## Already set in the context of the set_folders() method above.
        pass

    def set_sync_folders (self):
        """See the documentation in class PIMDB"""

        raise NotImplementedError

    def prep_for_sync (self, dbid, pname, dr):
        ## FIXME: Should read the group name and id of the sync folder and set
        ## up the sync folder variable, etc.

        pass

    ##
    ## Now the non-abstract methods and internal methods
    ##

    def get_user (self):
        return self.user

    def set_user (self, user):
        self.user = user

    def get_cs (self):
        return self.pw

    def set_cs (self, pw):
        self.pw = pw

    def get_service (self):
        """Return the Google People API service object."""
        return self.service

    def set_service (self, service):
        self.service = service

    ## Keep get_gdc/set_gdc as aliases for code that still references them
    ## (e.g. folder_gc.py during transition)
    def get_gdc (self):
        return self.get_service()

    def set_gdc (self, svc):
        self.set_service(svc)

    def gc_init (self):
        """Authenticate with Google and create the People API service.

        Uses InstalledAppFlow for the OAuth2 dance.  Tokens are cached
        in a pickle file in the user directory so subsequent runs don't
        require re-authorization.
        """
        logging.info('Attempting to log into Google...')
        user_dir = self.get_config().get_user_dir()
        token_file = os.path.join(user_dir, '%s.token.pickle' % self.get_user())
        cs_file = os.path.abspath(os.path.expanduser(self.get_cs()))

        creds = None

        # Load cached token if it exists
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)

        # If there are no valid credentials, do the OAuth dance
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logging.info('Refreshing expired access token...')
                creds.refresh(Request())
            else:
                logging.info('Starting OAuth2 authorization flow...')
                if not os.path.exists(cs_file):
                    logging.error('Client secrets file not found: %s', cs_file)
                    raise FileNotFoundError(
                        'OAuth2 client secrets file not found: %s' % cs_file)
                flow = InstalledAppFlow.from_client_secrets_file(
                    cs_file, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
            logging.info('Credentials saved to %s', token_file)
        else:
            logging.info('Using cached access token...')

        service = build('people', 'v1', credentials=creds)
        self.set_service(service)

    def _list_contact_groups (self):
        """Fetch all contact groups from the People API.  Returns a list
        of contactGroup resource dicts."""

        results = self.get_service().contactGroups().list(
            pageSize=1000).execute()
        return results.get('contactGroups', [])

    def get_groups_feed (self):
        """Compatibility wrapper — returns the list of contact groups.
        Old code called this and expected a feed object with .entry;
        new code returns a list of group resource dicts."""

        return self._list_contact_groups()

    def print_groups (self):
        groups = self._list_contact_groups()

        if not groups:
            print('No groups for user')
        for i, group in enumerate(groups):
            print('\n%s %s' % (i+1, group.get('name', '(unnamed)')))
            print('  Group ID: %s' % group['resourceName'])
            if group.get('memberCount'):
                print('  Members: %s' % group['memberCount'])

    def find_group (self, title, ret_type='id'):
        """This routine will directly look up the server using the API and try
        to find the specified group by name.

        Takes a group title, and returns the Group ID if found. Returns
        None if the group cannot be found.
        """

        groups = self._list_contact_groups()

        if not groups:
            logging.info('\nGroup (%s) not found: there are no groups!',
                          title)
            return None

        for group in groups:
            if group.get('name') == title:
                if ret_type == 'entry':
                    return group
                else:
                    return group['resourceName']

        return None

    def new_feed (self):
        """No longer applicable — batch operations use different API.
        Raises NotImplementedError to catch any old code paths."""
        raise NotImplementedError(
            'new_feed() is obsolete. Use People API batch methods instead.')

    def exec_batch (self, batch_feed, extra_headers=None):
        """No longer applicable — batch operations use different API.
        Raises NotImplementedError to catch any old code paths."""
        raise NotImplementedError(
            'exec_batch() is obsolete. Use People API batch methods instead.')
