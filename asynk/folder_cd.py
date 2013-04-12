##
## Created : Wed Apr 03 12:59:03 IST 2013
##
## Copyright (C) 2013 Sriram Karra <karra.etc@gmail.com>
##
## This file is part of ASynK
##
## ASynK is free software: you can redistribute it and/or modify it under
## the terms of the GNU Affero General Public License as published by the
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

from   folder         import Folder
from   contact_cd     import CDContact
from   vobject        import vobject
from   caldavclientlibrary.protocol.url                 import URL
from   caldavclientlibrary.protocol.webdav.definitions  import davxml
from   caldavclientlibrary.protocol.carddav.definitions import carddavxml

import logging

class CDContactsFolder(Folder):
    def __init__ (self, db, fid, gn, root_path):
        Folder.__init__(self, db)

        self.set_itemid(fid)
        self.set_name(gn)
        self.set_root_path(root_path)
        self.set_type(Folder.CONTACT_t)
        self.reset_contacts()

    ##
    ## Internal and helper functions
    ##        

    def __str__ (self):
        ret = 'Contacts'

        return ('%s.\tName: %s;\tGID: %s;\t' % (ret, self.get_name(),
                                                self.get_itemid()))

    def get_batch_size (self):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def prep_sync_lists (self, destid, sl, last_sync_stop=None, limit=0):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def get_itemids (self, pname, destid):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def find_item (self, itemid):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def find_items (self, itemids):
        """See the documentation in folder.Folder"""

        sess = self.get_db().session()
        results = sess.multiGet(URL(path=self.get_itemid()), itemids,
                                (davxml.getetag, carddavxml.address_data))

        ret = []
        for key, item in results.iteritems():
            etag = item.getNodeProperties()[davxml.getetag]
            vcf  = item.getNodeProperties()[carddavxml.address_data]

            vco = vobject.readOne(vcf.text)
            ret.append(CDContact(self, vco=vco, itemid=key))

        return ret

    def batch_create (self, src_sl, src_dbid, items):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def batch_update (self, src_sl, src_dbid, items):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def writeback_sync_tags (self, pname, items):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def bulk_clear_sync_flags (self, label_re=None):
        """See the documentation in folder.Folder"""

        raise NotImplementedError


    ##
    ## Internal and helper functions
    ##        

    def reset_contacts (self):
        self.contacts = {}

    def get_contacts (self):
        return self.contacts

    def add_contact (self, bbc):
        self.contacts.update({bbc.get_itemid() : bbc})

    def _refresh_contacts (self):
        logging.debug('Refreshing Contacts for folder %s...',
                      self.get_name())
        self.reset_contacts()
        ## Now fetch from server

        sess  = self.get_db().session()
        path  = URL(url=self.get_itemid())
        props = (davxml.getetag,)
        items = sess.getPropertiesOnHierarchy(path, props)

        for uri in items:
            if uri == path.toString().strip():
                continue

            ## FIXME: We also need to ensure we skip any contained
            ## collections, and only deal with bona fide vCard files.

            result = sess.readData(URL(url=uri))
            if not result:
                logging.error('Could not GET URI: "%s"', uri)
                continue
            data, etag = result

            vco = vobject.readOne(data)
            cdc = CDContact(self, vco=vco, itemid=uri)
            self.add_contact(cdc)
            logging.debug('Successfully fetched and added contact: %s',
                          uri)

        logging.debug('Refreshing Contacts for folder %s..done.',
                      self.get_name())

    def show (self, detailed=False):
        self._refresh_contacts()
        cons = self.get_contacts()
        logging.info('Total contained contacts: %d', len(cons.keys()))
        logging.info('Items in brief: ')

        for itemid, con in cons.iteritems():
            if detailed:
                logging.info('Printing Contact: %s', con.get_disp_name())
                logging.info('%s', con)
            else:
                logging.info('  Name: %-25s Gender: %s Itemid: %s',
                             con.get_disp_name(), con.get_gender(), itemid)

    def get_root_path (self):
        return self._get_prop('root_path')

    def set_root_path (self, root_path):
        self._set_prop('root_path', root_path)

    def put_item (self, name, data, content_type):
        path = URL(url="%s%s" % (self.get_itemid(), name))
        res = self.get_db().session().writeData(path, data, content_type)

        ## FIXME: How do we handle errors?
