##
## Created : Wed Apr 03 12:59:03 IST 2013
##
## Copyright (C) 2013 Sriram Karra <karra.etc@gmail.com>
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


from   folder         import Folder
from   contact_cd     import CDContact
from   caldavclientlibrary.protocol.url                 import URL
from   caldavclientlibrary.protocol.http.util           import HTTPError
from   caldavclientlibrary.protocol.webdav.definitions  import davxml
from   caldavclientlibrary.protocol.carddav.definitions import carddavxml

import logging, vobject

class CDContactsFolder(Folder):
    def __init__ (self, db, fid, gn, root_path):
        Folder.__init__(self, db)

        if fid[-1] != '/':
            fid += '/'

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

        raise 100

    def prep_sync_lists (self, destid, sl, updated_min=None, cnt=0):
        """See the documentation in folder.Folder"""

        pname = sl.get_pname()
        conf  = self.get_config()
        pdb1id = conf.get_profile_db1(pname)
        oldi  = conf.get_itemids(pname)
        curi  = self.get_itemids(pname, destid)

        kss = curi.keys()
        for x, y in oldi.iteritems():
            if not x in kss and not y in kss:
                logging.debug('Del      Carddav Contact: %s:%s', x, y)
                if pdb1id == self.get_dbid():
                    sl.add_del(x, y)
                else:
                    sl.add_del(y,x)

        stag = conf.make_sync_label(pname, destid)

        if not updated_min:
            updated_min = conf.get_last_sync_stop(pname)

        # Note: crdid refers to the CardDAV server item id for the contact,
        # and the remid refers to the ID on the other end of the sync
        # profile.
        for i, (crdid, item) in enumerate(self.get_contacts().iteritems()):
            try:
                label, remid = item.get_sync_tags(stag)[0]
            except IndexError, e:
                label = None
                remid = None

            name = 'No Name'
            if item.get_name():
                name = item.get_name()
            elif item.get_disp_name():
                name = item.get_disp_name()

            if not remid:
                # New contact
                logging.debug('New      CardDAV Contact: %20s %s', 
                              name, crdid)
                sl.add_new(crdid)
            else:
                if item.get_updated(iso=True) > updated_min:
                    logging.debug('Modified CardDAV Contact: %20s %s', 
                                  name, crdid)
                    sl.add_mod(crdid, remid)
                else:
                    sl.add_unmod(crdid)

            # FIXME: We should really storing the etags here...
            sl.add_etag(crdid, item.get_etag())

        logging.debug('Total Contacts   : %5d', len(curi))

    def get_itemids (self, pname, destid):
        """See the documentation in folder.Folder"""

        self._refresh_contacts()
        ret = {}
        stag = self.get_config().make_sync_label(pname, destid)
        for locid, con in self.get_contacts().iteritems():
            if stag in con.get_sync_tags():
                t, remid = con.get_sync_tags(stag)[0]
                ret.update({locid : remid})

        return ret

    def del_itemids (self, itemids):
        sess = self.get_db().session()
        for itemid in itemids:
            try:
                sess.deleteResource(URL(url=self.item_path(itemid)))
                self.del_contact(itemid)
                logging.info('Deleted CardDAV server contact %s...', itemid)
            except HTTPError, e:
                logging.error('Could not delete itemid: %s (%s)', itemid, e)


    def item_path (self, itemid):
        if itemid[0] != '/':
            iid = self.get_itemid()
            if iid[-1] != '/':
                iid += '/'
            itemid = iid + itemid + '.vcf'

        return itemid

    def find_item (self, itemid):
        """See the documentation in folder.Folder"""

        sess = self.get_db().session()
        result = sess.readData(URL(path=self.item_path(itemid)))
        if not result:
            return None

        data, _ignore_etag = result

        try:
            itemid = CDContact.normalize_cdid(itemid)
            return CDContact(self, vco=vobject.readOne(data), itemid=itemid)
        except Exception, e:
            logging.error('Error (%s) parsing vCard object for %s',
                          e, itemid)
            raise

    def find_items (self, itemids):
        """See the documentation in folder.Folder"""

        sess = self.get_db().session()
        ids = [self.item_path(x) for x in itemids]
        results = sess.multiGet(URL(path=self.get_itemid()), ids,
                                (davxml.getetag, carddavxml.address_data))

        ret = []
        for key, item in results.iteritems():
            etag = item.getNodeProperties()[davxml.getetag]
            vcf  = item.getNodeProperties()[carddavxml.address_data]

            try:
                key = CDContact.normalize_cdid(key)
                cd = CDContact(self, vco=vobject.readOne(vcf.text), itemid=key)
            except Exception, e:
                logging.error('Error (%s) parsing vCard object for %s',
                              e, key)
                raise

            cd.set_etag(etag.text)
            ret.append(cd)

        return ret

    def batch_create (self, src_sl, src_dbid, items):
        """See the documentation in folder.Folder"""

        my_dbid = self.get_dbid()
        c       = self.get_config()
        pname   = src_sl.get_pname()

        src_sync_tag = c.make_sync_label(src_sl.get_pname(), src_dbid)
        dst_sync_tag = c.make_sync_label(src_sl.get_pname(), my_dbid)

        success = True
        for item in items:

            ## CardDAV does not support a multiput operation. So we will have
            ## to PUT the damn items one at a time. What kind of a standard is
            ## this, anyway?

            con_itemid = item.get_itemid_from_synctags(pname, 'cd')
            cd = CDContact(self, con=item, con_itemid=con_itemid)
            cd.update_sync_tags(src_sync_tag, item.get_itemid(), save=True)
            self.add_contact(cd)            

            item.update_sync_tags(dst_sync_tag, cd.get_itemid())

            logging.info('Successfully created CardDAV entry for %30s (%s)',
                         cd.get_disp_name(), cd.get_itemid())

        return True

    def batch_update (self, src_sl, src_dbid, items):
        """See the documentation in folder.Folder"""

        my_dbid = self.get_dbid()
        c       = self.get_config()
        pname   = src_sl.get_pname()

        src_sync_tag = c.make_sync_label(pname, src_dbid)
        dst_sync_tag = c.make_sync_label(pname, my_dbid)

        cons = self.get_contacts()

        ## FIXME: We will try to overwrite using the etags we had fetched just
        ## a fe moments back. It could still fail; and the error handling
        ## needs to be robust ... but it is not

        success = True

        for item in items:
            tag, href = item.get_sync_tags(dst_sync_tag)[0]
            ## FIXME: Some times we might find it expedient to force a
            ## "update" without the contact being present int he remote. If
            ## that happens the next line will throw an KeyError. You are
            ## warned. 
            con_old = cons[href]
            con_itemid = item.get_itemid_from_synctags(pname, 'cd')
            con_new = CDContact(self, con=item, con_itemid=con_itemid)

            con_new.set_uid(con_old.get_uid())
            con_new.update_sync_tags(src_sync_tag, item.get_itemid())

            try:
                con_new.save(etag=con_old.get_etag())
                logging.info('Successfully updated CardDAV entry for %30s (%s)',
                             con_new.get_disp_name(), con_new.get_itemid())
            except HTTPError, e:
                logging.error('Error (%s). Could not update CardDAV entry %s',
                              e, con_new.get_disp_name())
                success = False

        return success

    def writeback_sync_tags (self, pname, items):
        """See the documentation in folder.Folder"""

        logging.info('Writing sync state to CardDAV server...')
        success = True
        for item in items:
            success = success and item.save()

        logging.info('Writing sync state to CardDAV server...done')
        return success

    def bulk_clear_sync_flags (self, label_re=None):
        """See the documentation in folder.Folder"""

        logging.info('folder_cd:bulk_clear_sync_tags: Not implemented yet.')
        return True


    ##
    ## Internal and helper functions
    ##        

    def reset_contacts (self):
        self.contacts = {}

    def get_contacts (self):
        return self.contacts

    def add_contact (self, bbc):
        self.contacts.update({bbc.get_itemid() : bbc})

    def del_contact (self, itemid):
        if itemid in self.contacts:
            del self.contacts[itemid]

    def _refresh_contacts (self):
        logging.debug('Refreshing Contacts for folder %s...',
                      self.get_name())
        self.reset_contacts()
        ## Now fetch from server

        sess  = self.get_db().session()
        path  = URL(url=self.get_itemid())
        props = (davxml.getetag,)
        items = sess.getPropertiesOnHierarchy(path, props)

        hrefs = [x for x in items.keys() if x != path.toString().strip()]
        etags = [items[x].get(davxml.getetag, "-") for x in items.keys()]

        cons  = self.find_items(hrefs)

        for con in cons:
            self.add_contact(con)
            logging.debug('Successfully fetched and added contact: %s',
                          con.get_disp_name())

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

    def put_item (self, name, data, content_type, etag=None):
        path = URL(url=name)
        res = self.get_db().session().writeData(path, data, content_type,
                                                etag=etag)

        return name

        ## FIXME: How do we handle errors?
