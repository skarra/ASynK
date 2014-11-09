##
## Created : Sat Apr 07 20:03:04 IST 2012
##
## Copyright (C) 2012, 2013 Sriram Karra <karra.etc@gmail.com>
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

import codecs, logging, re, string, traceback
from   folder     import Folder
from   contact_bb import BBContact, BBDBParseError
import pimdb_bb, utils

class BBContactsFolder(Folder):    
    default_folder_id = 'default'

    def __init__ (self, db, fn, store=None):
        logging.debug('New BBContactsFolder: %s', fn)

        Folder.__init__(self, db, store)
        
        self.set_clean()
        self.set_type(Folder.CONTACT_t)
        self.set_itemid(fn)
        self.set_name(fn)

        self.reset_contacts()

    def __del__ (self):
        if self.is_dirty():
            self.get_store().save_file()

    ##
    ## Implementation of the abstract methods inherited from Folder
    ##

    def get_batch_size (self):
        return 1000

    def prep_sync_lists (self, destid, sl, updated_min=None, cnt=0):
        pname = sl.get_pname()
        conf  = self.get_config()
        pdb1id = conf.get_profile_db1(pname)
        oldi  = conf.get_itemids(pname)
        stag  = conf.make_sync_label(pname, destid)

        ## Sort the DBIds so dest1 has the 'lower' ID
        db1 = self.get_dbid()
        if db1 > destid:
            db2 = db11
            db1 = destid
        else:
            db2 = destid

        if not updated_min:
            ## Note that we only perform a string operation for comparing
            ## times. This rides on a big assumption that both the timestamps
            ## are in UTC
            updated_min = self.get_config().get_last_sync_stop(pname)
            updated_min = string.replace(updated_min, r'+', ' ')
            updated_min = string.replace(updated_min, r'T', ' ')

        i = 0
        logging.debug('destid: %s', destid)

        newi = {}
        for iid, con in self.get_contacts().iteritems():
            i += 1
            if stag in con.get_sync_tags():
                t, did = con.get_sync_tags(stag)[0]
                newi.update({iid : did})
                upd = con.get_updated()
                if not upd:
                    logging.error('Skipping entry %s without updated field.',
                                  iid)
                else:
                    if upd > updated_min:
                        logging.debug('Modified BBDB Contact: %20s %s', 
                                      con.get_name(), iid)
                        sl.add_mod(iid, did)
                    else:
                        sl.add_unmod(iid)
            else:
                logging.debug('New      BBDB Contact: %20s %s', 
                              con.get_name(), iid)
                sl.add_new(iid)

        kss = newi.keys()
        for x, y in oldi.iteritems():
            ## FIXME: The following could lead to virtually undebuggable
            ## problem if same item ID is used across two different sources
            ## and stores. But what are the chances, eh?
            
            if not x in kss and not y in kss:
                logging.debug('Del      BBDB Contact: %s:%s', x, y)
                if pdb1id == self.get_dbid():
                    sl.add_del(x, y)
                else:
                    sl.add_del(y,x)

    def get_itemids (self, pname, destid):
        """See documentation in folder.py"""

        ret = {}
        stag = self.get_config().make_sync_label(pname, destid)
        for locid, con in self.get_contacts().iteritems():
            if stag in con.get_sync_tags():
                t, remid = con.get_sync_tags(stag)[0]
                ret.update({locid : remid})

        return ret

    def find_item (self, itemid):
        """See documentation in folder.py"""

        return self.get_contacts()[itemid]

    def find_items (self, itemids):
        """See documentation in folder.py"""

        return [self.find_item(i) for i in itemids]

    def batch_create (self, src_sl, src_dbid, items, op='create'):
        """See the documentation in folder.Folder"""

        my_dbid = self.get_dbid()
        c       = self.get_config()
        pname   = src_sl.get_pname()

        src_tag = c.make_sync_label(pname, src_dbid)
        dst_tag = c.make_sync_label(pname, my_dbid)

        if len(items) > 0:
            self.set_dirty()

        for item in items:
            try:
                con_itemid = item.get_itemid_from_synctags(pname, 'bb')
                bbc = BBContact(self, con=item, con_itemid=con_itemid)
                bbc.update_sync_tags(src_tag, item.get_itemid())
                bbc.set_updated(pimdb_bb.BBPIMDB.get_bbdb_time())
                self.add_contact(bbc)

                item.update_sync_tags(dst_tag, bbc.get_itemid())
                logging.info('Successfully %sd BBDB entry for %30s (%s)',
                             op, bbc.get_name(), bbc.get_itemid())
            except BBDBParseError, e:
                logging.error('Could not instantiate BBDBContact object: %s',
                              str(e))

        try:
            self.get_store().save_file()
        except Exception, e:
            logging.error('bb:bc: Could not save BBDB folder %s (%s)',
                          self.get_name(), str(e))
            self.get_store().restore_backup()
            logging.debug(traceback.format_exc())
            return False

        return True

    def batch_update (self, sync_list, src_dbid, items):
        """See the documentation in folder.Folder. sync_list is not really
        needed and we should nuke it some time"""

        ## For BBDB updating records like this is the same as creating them,
        ## because when a contact entry is added to the contact list using
        ## 'add_contact', the older object is replaced using the new object
        ## and all is good. The fact that we do a delayed write also
        ## helps. Life would be a lot more complicated if we had to do live
        ## updates to the disk

        return self.batch_create(sync_list, src_dbid, items, op='update')

    def writeback_sync_tags (self, pname, items):
        logging.debug('bb:wst: Dirty flag: %s', self.is_dirty())
        try:
            self.get_store().save_file()
            return True
        except Exception, e:
            logging.error('bb:wst: Could not save BBDB folder %s (%s)',
                          self.get_name(), str(e))
            self.get_store().restore_backup()
            logging.debug(traceback.format_exc())
            return False

    def bulk_clear_sync_flags (self, label_re=None):
        self.get_store().create_backup(pname='clear_sync')

        if not label_re:
            label_re = 'asynk:[a-z][a-z]:id'

        ret = True
        cnt = 0
        for i, c in self.get_contacts().iteritems():
            try:
                cnt += 1 if c.del_sync_tags(label_re) else 0
            except Exception, e:
                logging.error('Caught exception (%s) while clearing flag: %s',
                              str(e), label_re)
                logging.error(traceback.format_exc())
                ret = False
    
        logging.info('Found %d contacts with matching sync tag(s). ', cnt)
        if cnt > 0:
            logging.info('Saving changes to disk...')

        try:
            self.set_dirty()
            self.get_store().save_file()
            if cnt > 0:
                logging.info('Saving changes to disk...done')
        except Exception, e:
            logging.error('Caught exception (%s) while saving BBDB folder',
                          str(e))
            self.get_store().restore_backup()
            ret = False

        return ret

    def __str__ (self):
        ret = 'Contacts'

        return ('%s.\tName: %s;\tGID: %s;\t' % (ret, self.get_name(),
                                                self.get_itemid()))

    ##
    ## Non-abstract methods of importance
    ##
    
    def save (self):
        self.get_store().save_file()

    def write_to_file (self, bbf, keep_open=True):
        """Write the folder's contacts to the specified file handle. bbf
        should be an open file handle. If the keep_open flag is False, this
        will close the file handle after completing its work."""

        for bbdbid, bbc in self.get_contacts().iteritems():
            con = bbc.init_rec_from_props()
            bbf.write('%s\n' % unicode(con))

        if not keep_open:
            bbf.close()

        self.set_clean()

    ##
    ## Internal and helper routines
    ##

    def is_dirty (self):
        return self._get_prop('dirty')

    def is_clean (self):
        return not self.is_dirty()

    def set_clean (self):
        return self._set_prop('dirty', False)

    def set_dirty (self):
        return self._set_prop('dirty', True)

    def add_contact (self, bbc):
        self.set_dirty()
        self.contacts.update({bbc.get_itemid() : bbc})

    def del_itemids (self, itemids):
        """Remove the specified from the contacts from this folder. Return
        value is a pair of (success, [failed entries])."""

        retv = True
        retf = []
        for itemid in itemids:
            try:
                con = self.contacts[itemid]
                logging.info('Deleting ID: %s; Name: %s...', itemid,
                             con.get_name())
                del self.contacts[itemid]
            except KeyError, e:
                retv = False
                retf.append(itemid)

        if len(itemids) > 0:
            self.save()
        return retv, retf

    def reset_contacts (self):
        self.contacts = {}

    def get_contacts (self):
        return self.contacts

    def find_contacts_by_name (self, cnt=0, name=None):
        """Return the list of contact objects in current folder that
        have a matching name. If name is None, all contacts objects
        are returned. If cnt is non-zero value then the first cnt 
        matching records are returned."""

        logging.debug('Looking for name %s in folder: %s ',
                        name, self.get_name())
        i = 0
        ret = []

        for iid, con in self.get_contacts().iteritems():
            if not name:
                ret.append(con)
            else:
                if (re.search(name, unicode(con.get_firstname()))
                    or re.search(name, unicode(con.get_name()))
                    or re.search(name, unicode(con.get_lastname()))):
                    ret.append(con)
            i += 1

            if cnt == i:
                break

        return ret

    def print_contacts (self, cnt=0, name=None):
        cons = self.find_contacts_by_name(cnt, name)
        for con in cons:
            logging.debug('%s', unicode(con))

        logging.debug('Printed %d contacts from folder %s', len(cons),
                      self.get_name())
