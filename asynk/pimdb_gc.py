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

import datetime, getopt, logging, sys, time, utils
import atom, gdata.contacts.data, gdata.contacts.client, base64

from   state        import Config
from   pimdb        import PIMDB, GoutInvalidPropValueError
from   folder       import Folder
from   folder_gc    import GCContactsFolder

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

class GCPIMDB(PIMDB):
    """GC object is a wrapper for a Google Contacts stream API."""

    def __init__ (self, config, user, pw):
        PIMDB.__init__(self, config)
        self.set_user(user)
        self.set_pw(pw)
        self.gc_init()

        self.set_folders()

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

        if not feed.entry:
            return ret

        for i, entry in enumerate(feed.entry):
            name = entry.content.text if entry.content else entry.title.text
            if not silent:
                logging.info(' %2d: Contacts Name: %-25s ID: %s',
                             i, name, entry.id.text)
            ret.append((entry.id.text, name, entry))

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
        groups = self.list_folders(silent=True)
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

    def get_pw (self):
        return self.pw

    def set_pw (self, pw):
        self.pw = pw

    def get_gdc (self):
        return self.gdc

    def set_gdc (self, gdc):
        self.gdc = gdc

    def gc_init (self):
        logging.info('Logging into Google...')

        gdc = gdata.contacts.client.ContactsClient(source='ASynK')
        gdc.ClientLogin(self.get_user(), self.get_pw(), gdc.source)
        self.set_gdc(gdc)

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
        feed = self.get_gdc().GetGroups()
        return feed

    def print_groups (self):
        feed = self.get_groups_feed()

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
