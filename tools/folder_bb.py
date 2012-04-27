##
## Created       : Sat Apr 07 20:03:04 IST 2012
## Last Modified : Fri Apr 27 17:00:18 IST 2012
##
## Copyright (C) 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
## 

import codecs, logging, re, string, traceback
from   folder     import Folder
from   contact_bb import BBContact
import pimdb_bb, utils

class BBDBFileFormatError(Exception):
    pass

class BBContactsFolder(Folder):    
    default_folder_id = 'default'

    def __init__ (self, db, fn):
        Folder.__init__(self, db)
        
        self.set_clean()
        self.set_itemid(fn)
        self.set_name(fn)

        self.contacts = {}
        self.parse_file()

    def __del__ (self):
        if self.is_dirty():
            self.save_file()

    ##
    ## Implementation of the abstract methods inherited from Folder
    ##

    def get_batch_size (self):
        return 1000

    def prep_sync_lists (self, destid, sl, updated_min=None, cnt=0):
        pname = sl.get_pname()
        stag = self.get_config().make_sync_label(pname, destid)

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

        i     = 0
        unmod = 0
        logging.debug('destid: %s', destid)

        for iid, con in self.get_contacts().iteritems():
            i += 1
            if stag in con.get_sync_tags():
                t, did = con.get_sync_tags(stag)[0]
                upd = con.get_updated()
                if not upd:
                    logging.error('Skipping entry %s without updated field.',
                                  iid)
                else:
                    if upd > updated_min:
                        sl.add_mod(iid, did)
                    else:
                        unmod += 1
            else:
                sl.add_new(iid)
                
        logging.debug('==== BB =====')
        logging.debug('num processed    : %5d', i)
        logging.debug('num total        : %5d', len(sl.get_entries()))
        logging.debug('num new          : %5d', len(sl.get_news()))
        logging.debug('num mod          : %5d', len(sl.get_mods()))
        logging.debug('num del          : %5d', len(sl.get_dels()))
        logging.debug('num unmod        : %5d', unmod)

    def find_item (self, itemid):
        """See documentation in folder.py"""

        return self.get_contacts()[itemid]

    def find_items (self, itemids):
        """See documentation in folder.py"""

        return [self.find_item(i) for i in itemids]

    def batch_create (self, src_sl, src_dbid, items):
        """See the documentation in folder.Folder"""

        my_dbid = self.get_dbid()
        c       = self.get_config()
        pname   = src_sl.get_pname()

        src_tag = c.make_sync_label(pname, src_dbid)
        dst_tag = c.make_sync_label(pname, my_dbid)

        if len(items) > 0:
            self.set_dirty()

        for item in items:
            bbc = BBContact(self, con=item)
            bbc.update_sync_tags(src_tag, item.get_itemid())
            bbc.set_updated(pimdb_bb.BBPIMDB.get_bbdb_time())
            self.add_contact(bbc)

            item.update_sync_tags(dst_tag, bbc.get_itemid())

        try:
            self.save_file()
        except Exception, e:
            logging.error('bb:bc: Could not save BBDB folder %s (%s)',
                          self.get_name(), str(e))
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

        return self.batch_create(sync_list, src_dbid, items)

    def writeback_sync_tags (self, pname, items):
        logging.debug('bb:wst: Dirty flag: %s', self.is_dirty())
        try:
            self.save_file()
            return True
        except Exception, e:
            logging.error('bb:wst: Could not save BBDB folder %s (%s)',
                          self.get_name(), str(e))
            logging.debug(traceback.format_exc())
            return False

    def bulk_clear_sync_flags (self, label_re=None):
        if not label_re:
            label_re = 'asynk:[a-z][a-z]:id'

        ret = True
        for i, c in self.get_contacts().iteritems():
            try:
                c.del_sync_tags(label_re)
            except Exception, e:
                logging.error('Caught exception (%s) while clearing flag: %s',
                              str(e), label_re)
                logging.error(traceback.format_exc())
                ret = False
    
        try:
            self.set_dirty()
            self.save_file()
        except Exception, e:
            logging.error('Caught exception (%s) while saving BBDB folder',
                          str(e))
            ret = False

        return ret

    def __str__ (self):
        ret = 'Contacts'

        return ('%s.\tName: %s;\tGID: %s;\t' % (ret, self.get_name(),
                                                self.get_itemid()))

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
        self.contacts.update({bbc.get_itemid() : bbc})

    def get_contacts (self):
        return self.contacts

    def set_file_format (self, ver):
        return self._set_prop('file_format', ver)

    def get_file_format (self):
        return self._get_prop('file_format')

    def parse_file (self, fn=None):
        if not fn:
            fn = self.get_name()

        logging.info('Parsing BBDB file %s...', fn)

        with codecs.open(fn, encoding='utf-8') as bbf:
            ff = bbf.readline()
            if re.search('coding:', ff):
                # Ignore first line if it is: ;; -*-coding: utf-8-emacs;-*-
                ff = bbf.readline()

            # Processing: ;;; file-format: 8
            res = re.search(';;; file-(format|version):\s*(\d+)', ff)
            if not res:
                bbf.close()
                raise BBDBFileFormatError('Unrecognizable format line: %s' % ff)

            ver = int(res.group(2))
            self.set_file_format(ver)

            if ver < 7:
                bbf.close()
                raise BBDBFileFormatError(('Need minimum file format ver 7. ' +
                                          '. File version is: %d' ) % ver)

            cnt = 0
            while True:
                ff = bbf.readline()
                if ff == '':
                    break

                if re.search('^;', ff):
                    continue

                c = BBContact(self, rec=ff.rstrip())
                self.add_contact(c)
                cnt += 1

        logging.info('Successfully parsed %d entries.', cnt)
        bbf.close()

    def save_file (self, fn=None):
        if not fn:
            fn = self.get_name() + '.out'

        logging.info('Saving BBDB Folder %s to file: %s...',
                     self.get_name(), fn)

        with codecs.open(fn, 'w', encoding='utf-8') as bbf:
            bbf.write(';; -*-coding: utf-8-emacs;-*-\n')
            bbf.write(';;; file-format: 7\n')

            for bbdbid, bbc in self.get_contacts().iteritems():
                con = bbc.init_rec_from_props()
                bbf.write('%s\n' % unicode(con))

        bbf.close()
        self.set_clean()

    def get_user_fields_as_string (self):
        # FIXME: Do something meanginful with this
        return 'mail-alias'

    def print_contacts (self, cnt=0):
        i = 0

        for iid, con in self.get_contacts().iteritems():
            logging.debug('%s', unicode(con))
            i += 1

            if cnt == i:
                break

        logging.debug('Printed %d contacts from folder %s', i,
                      self.get_name())

    ##
    ## Some class methods
    ##

    @classmethod
    def get_default_folder_id (self):
        return self.default_folder_id
