##
## Created : Thu Jul 07 14:47:54 IST 2011
##
## Copyright (C) 2011, 2012, 2013 by Sriram Karra <karra.etc@gmail.com>
##
## This file is part of ASynK
##
## ASynK is free software: you can redistribute it and/or modify it under
## the terms of the GNU Affero GPL (GNU AGPL) as published by the
## Free Software Foundation, version 3 of the License
##
## ASynK is distributed in the hope that it will be useful, but WITHOUT
## ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
## FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
## License for more details.
##
## You should have a copy of the license in the doc/ directory of ASynK.  If
## not, see <http://www.gnu.org/licenses/>.
##
## ####
##

import base64, datetime, getopt, httplib2, json, logging, os, sys, threading, time
import utils, webbrowser
from   urlparse import urlparse
import SimpleHTTPServer, SocketServer

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from   state        import Config
from   pimdb        import PIMDB, GoutInvalidPropValueError
from   folder       import Folder
from   folder_gc    import GCContactsFolder

CONTACTS_SCOPE_RO = 'https://www.googleapis.com/auth/contacts.readonly'
CONTACTS_SCOPES = [CONTACTS_SCOPE_RO]

def patched_post(client, entry, uri, auth_token=None, converter=None,
                 desired_class=None, **kwargs):
    if converter is None and desired_class is None:
        desired_class = entry.__class__
    http_request = atom.http_core.HttpRequest()
    entry_string = entry.to_string(gdata.client.get_xml_version(client.api_version))
    entry_string = entry_string.replace('ns1', 'gd')
    http_request.add_body_part(
        entry_string,
        'application/atom+xml')
    return client.request(method='POST', uri=uri, auth_token=auth_token,
                          http_request=http_request, converter=converter,
                          desired_class=desired_class, **kwargs)

class MyAuthToken:
    def __init__ (self, config, credentials):
        self.config = config
        self.creds = credentials

    def modify_request (self, http_request):
        self.creds.apply(http_request.headers)

        debug = self.config.get_gc_logging()
        if debug:
            logging.debug(http_request._dump())

class GCPIMDB(PIMDB):
    """GC object is a wrapper for a Google Contacts stream API."""

    def __init__ (self, config, user, pw):
        """
        config - an instantitation of the Config class specific to ASynK
        user - username, typically an @gmail.com email address
        pw   - historically this was the plaintext password. However
               since deprecation of plain text authn by Google, this should
               be the file name of OAuth "client secrets" json file. This can
               be quite confusing - this is not tied to a specific username;
               it refers to the AsynK program itself. The client information
               here will be used to dynamically get credentials to access the
               account after authz from user - those dynamic credentials
               (access_tokens) will be stored in a different location and are
               separate from this client secrets file. I am sorry; not sorry :)
        """
        self.server = None

        PIMDB.__init__(self, config)
        self.set_user(user)
        self.set_cs(pw)
        self.gc_init()

        self.set_folders()

    def __del__ (self):
        if not self.server is None:
            self.server.shutdown()

    ##
    ## First implementation of the abstract methods of PIMDB.
    ##

    def get_dbid (self):
        """See the documentation in class PIMDB"""

        return 'gc'

    def list_folders (self, silent=False):
        """Apart from doing the usual thing, this also retusn some good
        stuff..."""

        ret = []
        feed = self.get_groups_feed()

        if not feed:
            return ret

        pageToken = None

        while True:
            results = feed.list(pageToken=pageToken).execute()

            for i, entry in enumerate(results['contactGroups']):
                name = entry['formattedName']
                if not silent:
                    logging.info(' %2d: Contacts Name: %-25s ID: %s',
                                 i, name, entry['resourceName'])
                ret.append((entry['resourceName'], name, entry))

            if len(ret) >= results['totalItems']:
                break

            pageToken = results['nextPageToken']

        return ret

    def new_folder (self, fname, ftype=None, storeid=None):
        if not ftype:
            ftype = Folder.CONTACT_t

        if ftype != Folder.CONTACT_t:
            logging.error('Only Contact Groups are supported at this time.')
            return None

        gn              = gdata.data.Name(name=fname)
        new_group       = gdata.contacts.data.GroupEntry(name=gn)
        new_group.title = atom.data.Title(text=fname)

        entry = self.get_gdc().create_group(new_group)

        if entry:
            logging.info('Successfully created group. ID: %s',
                         entry.id.text)
            f = GCContactsFolder(self, entry.id.text, gn, entry)
            self.add_contacts_folder(f)
            return entry.id.text
        else:
            logging.error('Could not create Group \'%s\'', gn)
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

        logging.info('Deleting the Group from Google''s servers...')
        self.get_gdc().delete_group(f.get_gcentry())
        logging.info('Deleting the Group from Google''s servers...done')

        self.remove_folder_from_lists(f, ftype)

    def set_folders (self):
        """See the documentation in class PIMDB"""

        logging.debug('Getting Group List to populate folders...')
        groups = self.list_folders(silent=False)
        for (gid, gn, gcentry) in groups:
            f = GCContactsFolder(self, gid, gn, gcentry)
            self.add_contacts_folder(f)
            logging.debug('Processing Folder: %s...', gn)
            if gn == 'System Group: My Contacts':
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

    def set_service (self, service):
        self.service = service

    def get_service (self):
        return self.service

    def _init_webserver (self, port):
        class MyRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
            def do_GET (self1):
                parsed_path = urlparse(self1.path)
                try:
                    params = dict([p.split('=') for p in parsed_path[4].split('&')])
                except:
                    params = {}

                self.authorized = True
                self.credentials = self.flow.step2_exchange(params)
                return params

        self.server = SocketServer.TCPServer(('', port), MyRequestHandler)

        logging.info('Starting to listen on port %d...', port)

        self.authorized = False
        thread = threading.Thread(target = self.server.serve_forever)
        thread.start()

    def gc_init (self):
        logging.info('Attempting to log into Google...')
        user_dir = self.get_config().get_user_dir()

        # Refresh and Access tokens for accessing the Contact list is stored
        # in a file on $user_dir, and is created automatically when the
        # authorization flow completes for the first time. The app's
        # credentials used to run the oauth dance should be specified at the
        # time of invocation of asynk (or through the sync profile).
        token_filen = os.path.abspath(os.path.join(user_dir,
                                                   'token.%s.json' % self.get_user()))

        creds = None
        if os.path.exists(token_filen):
            creds = Credentials.from_authorized_user_file(token_filen,
                                                          CONTACTS_SCOPES)
            # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.get_cs(), CONTACTS_SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_filen, 'w') as token:
                token.write(creds.to_json())

        self.creds = creds
        self.set_service(build('people', 'v1', credentials=self.creds))

        ## Mon Jun 15 16:07:56 IST 2015 Not sure why this code is commented
        ## out, and if we need it to be here at all ... Hm.

        # if not self.get_config().get_gid():
        #     logging.info('First use of application. Creating group...')
        #     gn = self.config.get_gn()
        #     if not gn:
        #         gn = 'Gout'
        #         self.config.set_gn(gn, False)
        #         logging.info('Using default Gmail Contacts Group: Gout')

        #     gc_gid = self.create_group(gn)
        #     self.config.set_gid(gc_gid)


    def get_groups_feed (self):
        return self.get_service().contactGroups()

    def print_groups (self):
        feed = self.get_groups_feed()
        print feed

        if not feed.entry:
            print 'No groups for user'
        for i, entry in enumerate(feed.entry):
            print '\n%s %s' % (i+1, entry.title.text)
            if entry.content:
                print '  Content: %s' % (entry.content.text)

            print '  Group ID: %s' % entry.id.text

    def find_group (self, title, ret_type='id'):
        """This routine will directly look up the server using the API and try
        to find the specified group by name.

        Takes a group title, and returns the Group ID if found. Returns
        None if the group cannot be found.
        """

        feed = self.get_gdc().GetGroups()

        if not feed.entry:
            logging.info('\nGroup (%s) not found: there are no groups!',
                          title)
            return None

        for i, entry in enumerate(feed.entry):
            if entry.title.text == title:
                if ret_type == 'entry':
                    return entry
                else:
                    return entry.id.text

        return None

    def new_feed (self):
        return gdata.contacts.data.ContactsFeed()

    def exec_batch (self, batch_feed, extra_headers=None):
        # return self.get_gdc().ExecuteBatch(
        #     batch_feed, gdata.contacts.client.DEFAULT_BATCH_URL,
        #     custom_headers=atom.client.CustomHeaders(**{'If-Match': '*'}))

        # As of May 2014 due to some change at Google's end the above
        # ExecuteBatch started failing. As usual Google failed to respond to
        # repeated requests to fix this. Eventually someone suggested a
        # workaround that worked. The method patched_post is take from here:
        # https://code.google.com/p/gdata-python-client/issues/detail?id=700#c9
        return patched_post(self.get_gdc(), batch_feed,
                            gdata.contacts.client.DEFAULT_BATCH_URL)
