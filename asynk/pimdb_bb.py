##
## Created : Sat Apr 07 18:52:19 IST 2012
##
## Copyright (C) 2012, 2013 by Sriram Karra <karra.etc@gmail.com>
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

import codecs, datetime, logging, os, re, shutil, string, time
from   pimdb        import PIMDB
from   folder       import Folder
from   folder_bb    import BBContactsFolder
from   contact_bb   import BBContact, BBDBParseError
import utils

class BBDBFileFormatError(Exception):
    pass

class ASynKBBDBUnicodeError(Exception):
    pass

## Note: Each BBDB File is a message store and there are one or more folders
## in it.
class MessageStore:
    """Represents a physical BBDB file, made up of one or more folders,
    each containing contacts."""

    def __init__ (self, db, name):
        self.atts = {}
        self.set_db(db)
        self.set_name(name)
        self.set_folders({})

        self.populate_folders()

    ##
    ## Some get and set routines
    ##

    def _get_att (self, key):
        return self.atts[key]

    def _set_att (self, key, val):
        self.atts[key] = val
        return val

    def get_db (self):
        return self._get_att('db')

    def set_db (self, db):
        return self._set_att('db', db)

    def get_config (self):
        return self.get_db().get_config()

    def get_name (self):
        return self._get_att('name')

    def set_name (self, name):
        return self._set_att('name', name)

    def get_store_id (self):
        return self.get_name()

    def get_folders (self):
        return self.folders

    def get_folder (self, name):
        if name in self.folders:
            return self.folders[name]
        else:
            return None

    def add_folder (self, f):
        self.folders.update({f.get_name() : f})

    def remove_folder (self, fold):
        """Remove a folder from the folder list by name."""

        del self.folders[fold.get_name()]
        self.save_file()

    def set_folders (self, fs):
        """fs has to be a dictionary"""

        self.folders = fs

    ##
    ## The Real Action
    ##

    def get_con_re (self):
        return self._get_att('con_re')

    def set_con_re (self, reg):
        return self._set_att('con_re', reg)

    def get_str_re (self):
        return self._get_att('str_re')

    def set_str_re (self, reg):
        return self._set_att('str_re', reg)

    def get_adr_re (self):
        return self._get_att('adr_re')

    def set_adr_re (self, reg):
        return self._set_att('adr_re', reg)

    def get_ph_re (self):
        return self._get_att('ph_re')

    def set_ph_re (self, reg):
        return self._set_att('ph_re', reg)

    def get_note_re (self):
        return self._get_att('note_re')

    def set_note_re (self, reg):
        return self._set_att('note_re', reg)

    def get_notes_re (self):
        return self._get_att('notes_re')

    def set_notes_re (self, reg):
        return self._set_att('notes_re', reg)

    def get_sync_tag_re (self):
        return self._get_att('sync_tag_re')

    def set_sync_tag_re (self, reg):
        return self._set_att('sync_tag_re', reg)

    @classmethod
    def get_def_folder_name (self):
        return 'default'

    def _set_regexes (self, ver=None):
        if not ver:
            ver     = self.get_file_format()
        regexes = self.get_db().get_regexes(ver)
        
        ## Now save some of the regexes for later use...
        self.set_con_re(regexes['con_re'])
        self.set_str_re(regexes['str_re'])
        self.set_adr_re(regexes['adr_re'])
        self.set_ph_re(regexes['ph_re'])
        self.set_note_re(regexes['note_re'])
        self.set_notes_re(regexes['notes_re'])

        # Compute and store away a regular expression to match sync tags in
        # the notes section
        c = self.get_config()
        p = c.get_label_prefix()
        s = c.get_label_separator()
        r = '%s%s\w+%s' % (p, s, s)
        self.set_sync_tag_re(r)

    def set_encoding (self, ver):
        return self._set_att('encoding', ver)

    def get_encoding (self):
        return self._get_att('encoding')

    def set_file_format (self, ver):
        return self._set_att('file_format', ver)

    def get_file_format (self):
        return self._get_att('file_format')

    def get_preamble (self):
        return self._get_att('preamble')

    def set_preamble (self, pre):
        return self._set_att('preamble', pre)

    def append_preamble (self, lines):
        try:
            pre = self.get_preamble()
        except KeyError, e:
            pre = ''

        pre += lines
        return self.set_preamble(pre)

    def _parse_preamble (self, fn, bbf):
        while True:
            ff = bbf.readline()
            if not ff:
                return None

            ff = ff.strip()
            if re.search('coding:', ff):
                # Ignore first line if such: ;; -*-coding: utf-8-emacs;-*-
                self.append_preamble(ff + "\n")
                continue

            if re.search('^\s*$', ff):
                continue

            if re.search('^;+$', ff):
                continue

            # Processing: ;;; file-format: 8
            res = re.search(';;; file-(format|version):\s*(\d+)', ff)
            if not res:
                bbf.close()
                raise BBDBFileFormatError('Unrecognizable format line: "%s"' % ff)
    
            self.append_preamble(ff + "\n")
            ver = res.group(2)
            self.set_file_format(ver)
    
            supported = self.get_db().supported_file_formats()
            if not ver in supported:
                bbf.close()
                raise BBDBFileFormatError(('Cannot process file "%s" '
                                           '(version %s). Supported versions '
                                           'are: %s' % (fn, ver, supported)))
    
            return ver

        return None

    def _set_default_preamble (self):
        ver = '9'               # There is no real difference in the
                                # preamble itself
        self.append_preamble(';; -*-coding: utf-8-emacs;-*-\n')
        self.append_preamble(';;; file-format: %s\n' % ver)
        self.set_file_format(ver)
        self.set_encoding("utf-8")

        return ver

    def parse_with_encoding (self, def_f, fn, encoding):
        """Folder object to which the parsed contacts will be added. fn is the
        name of the BBDB file/message store. encoding is a string representing
        a text encoding such as utf-8, latin-1, etc."""

        if not os.path.exists(fn):
            utils.touch(fn)

        with codecs.open(fn, encoding=encoding) as bbf:
            ver = self._parse_preamble(fn, bbf)
            if not ver:
                ## We encountered a blank BBDB file.
                ver = self._set_default_preamble()

            ## Now fetch and set up the parsing routines specific to the file
            ## format 
            self._set_regexes(ver)

            cnt = 0
            while True:
                try:
                    ff = bbf.readline().strip()
                except UnicodeDecodeError, e:
                    ## We got the encoding wrong. We will have to drop
                    ## everything we have done, and start all over again.  At
                    ## a later stage, we could optimize by skipping over
                    ## whatever we have read so far, but then we will need to
                    ## evalute if the parsed strings will be in the same
                    ## encoding or not. Tricky and shady business, this.
                    raise ASynKBBDBUnicodeError('')

                if re.search('^\s*$', ff):
                    break

                if re.search('^;', ff):
                    self.append_preamble(ff + "\n")
                    continue

                try:
                    c  = BBContact(def_f, rec=ff.rstrip())
                except BBDBParseError, e:
                    logging.error('Could not parse BBDB record: %s', ff)

                    raise BBDBFileFormatError(('Cannot proceed with '
                                              'processing file "%s" ') % fn)

                fon = c.get_bbdb_folder()

                if fon:
                    f = self.get_folder(fon)
                    if not f:
                        f = BBContactsFolder(self.get_db(), fon, self)
                        self.add_folder(f)
                    f.add_contact(c)
                else:
                    def_f.add_contact(c)

                cnt += 1

            return bbf, cnt

    def populate_folders (self, fn=None):
        """Parse a BBDB file contents, and create folders of contacts."""

        ## BBDB itself is not structured as logical folders. The concept of a
        ## BBDB folder is overlayed by ASynK. Any contact with a notes field
        ## with key called 'folder' (or as configured in config.json), is
        ## assigned to a folder of that name. If an object does not have a
        ## folder note, it is assgined to the default folder.

        ## This routine parses the BBDB file by reading one line at at time
        ## from top to bottom. Due to a limitation in how the Contact() and
        ## Folder() classes interact, we have to pass a valid Folder object to
        ## the Contact() constructor. So the way we do this is we start by
        ## assuming the contact is in the default folder. After successful
        ## parsing, if the folder name is available in the contact, we will
        ## move it from the dfault folder to that particular folder.

        if not fn:
            fn = self.get_name()

        fn = utils.abs_pathname(self.get_config(), fn)
        logging.info('Parsing BBDB file %s...', fn)

        def_fn = self.get_def_folder_name()
        def_f = BBContactsFolder(self.get_db(), def_fn, self)
        self.add_folder(def_f)
        failed = True

        for encoding in self.get_db().get_text_encodings():
            self.set_encoding(encoding)
            try:
                logging.info('Parsing BBDB Store with encoding %s...',
                             encoding)
                bbf, cnt = self.parse_with_encoding(def_f, fn,
                                                    encoding=encoding)
                logging.info('Parsing BBDB Store with encoding %s...Success',
                             encoding)
                failed = False
                break
            except ASynKBBDBUnicodeError, e:
                ## Undo all state, and start afresh, pretty much.
                failed = True
                self.set_file_format(0)
                self.set_preamble('')
                self.set_folders({})
                def_f = BBContactsFolder(self.get_db(), def_fn, self)
                self.add_folder(def_f)
                logging.info('Parsing BBDB Store with encoding %s...Failed',
                             encoding)

        if failed:
            ## Oops, we failed to parse the file fully even once...
            raise BBDBFileFormatError('Cannot process file "%s": unable to '
                                      'ascerain text encoding.' % fn)

        logging.info('Successfully parsed %d entries.', cnt)
        bbf.close()

    def save_file (self, fn=None):
        if not fn:
            fn = self.get_name()

        fn = utils.abs_pathname(self.get_config(), fn)
        logging.info('Saving BBDB File %s...', fn)

        with codecs.open(fn, 'w', encoding=self.get_encoding()) as bbf:
            bbf.write(self.get_preamble())

            for name, f in self.get_folders().iteritems():
                f.write_to_file(bbf)

        logging.info('Saving BBDB File %s...done', fn)

    def prep_for_sync (self, pname):
        self.create_backup(pname)

    def create_backup (self, pname):
        """Make a backup of the BBDB store into the backup directory"""

        conf = self.get_config()
        bdir = os.path.join(conf.get_user_dir(), conf.get_backup_dir())

        stamp = string.replace(str(datetime.datetime.now()), ' ', '.')
        stamp = string.replace(stamp, ':', '-')
        backup_name = os.path.join(bdir, 'bbdb_backup.' + pname + '.' + stamp)

        src = self.get_name()
        src = utils.abs_pathname(self.get_config(), src)

        logging.info('Backedup BBDB Store (%s) to file: %s', src, backup_name)
        shutil.copy2(src, backup_name)
        
        self.set_last_backup_name(backup_name)

    def restore_backup (self):
        """This method is invoked if something went wrong and the current sync
        operation needs to be unwound. In such a case we will restore the
        datastore to the backup made at the beginning of the current sync."""

        backup = self.get_last_backup_name()
        store  = self.get_name()
        logging.info('Restoring BBDB Store (%s) from backup... (%s)',
                     store, backup)
        shutil.copy2(backup, store)
        logging.info('Restoring BBDB Store (%s) from backup...done (%s)',
                     store, backup)

    def get_last_backup_name (self):
        return self._last_backup

    def set_last_backup_name (self, backup):
        self._last_backup = backup

class BBPIMDB(PIMDB):
    """Wrapper class over the BBDB, by implementing the PIMDB abstract
    class."""

    def __init__ (self, config, def_fn):
        PIMDB.__init__(self, config)

        ## Setup some BBDB specific config parameters
        enc = self.get_db_config()['text_encodings']
        self.set_text_encodings(enc)

        ## For now the only version we support is file format 7. But in the
        ## near future ...
        self.set_regexes({})
        self._set_regexes_ver6()
        self._set_regexes_ver7()
        self._set_regexes_ver9()

        self.set_msgstores({})
        def_ms = self.add_msgstore(def_fn)
        self.set_def_msgstore(def_ms)
        self.set_folders()
        self.set_def_folders()

    ##
    ## First implementation of the abstract methods of PIMDB.
    ##

    def supported_file_formats (self):
        return self.get_regexes().keys()

    def get_dbid (self):
        """See the documentation in class PIMDB"""

        return 'bb'

    def set_text_encodings (self, name):
        self.text_encodings = name
        return name

    def get_text_encodings (self):
        return self.text_encodings

    def get_msgstore (self, name):
        return self.msgstores[name]

    def get_msgstores (self):
        return self.msgstores

    def set_msgstores (self, ms):
        self.msgstores = ms
        return ms

    def get_def_msgstore (self):
        return self.def_msgstore

    def set_def_msgstore (self, ms):
        self.def_msgstore = ms
        return ms

    def add_msgstore (self, ms):
        """Add another messagestore to the PIMDB. ms can be either a string,
        or an object of type MessageStore. If it is a string, then the string
        is interpreted as the fully expanded name of a BBDB file, and it is
        parsed accordingly. If it is an object already, then it is simply
        appended to the existing list of stores."""

        if isinstance(ms, MessageStore):
            self.msgstores.update({ms.get_name(): ms})
        elif isinstance(ms, basestring):
            ms = MessageStore(self, ms)
            self.msgstores.update({ms.get_name() : ms})
        else:
            logging.error('Unknown type (%s) in argument to add_msgstore %s',
                          type(ms), ms)
            return None

        return ms

    def get_regexes (self, ver=None):
        if ver:
            return self.regexes[ver]
        else:
            return self.regexes

    def set_regexes (self, rg):
        self.regexes = rg
        return rg

    def add_regexes (self, ver, value):
        self.regexes.update({ver : value})

    def new_folder (self, fname, ftype=None, storeid=None):
        logging.debug('bb:new_folder(): fname: %s; ftype: %s', fname, ftype)
        if not ftype:
            ftype = Folder.CONTACT_t

        if ftype != Folder.CONTACT_t:
            logging.erorr('Only Contact Groups are supported at this time.')
            return None

        if storeid:
            ms = self.get_msgstore(storeid)
        else:
            ms = self.get_def_msgstore()

        f  = BBContactsFolder(self, fname, ms)
        ms.add_folder(f)

        return f

    @classmethod
    def new_store (self, fname, ftype=None):
        """See the documentation in class PIMDB.
        fname should be a filename in this case.
        """

        ## FIXME: This routine should really be one of the cases in the
        ## constructor. 

        with codecs.open(fname, 'w', encoding='utf-8') as bbf:
            bbf.write(';; -*-coding: utf-8-emacs;-*-\n')
            bbf.write(';;; file-format: 7\n')
            bbf.close()

        logging.info('Successfully Created BBDB file: %s', fname)

        # # The following can be uncommented when this stuff is also put into
        # # the constructor

        # ms = MessageStore(self, fname)
        # self.add_msgstore(ms)

    def show_folder (self, gid):
        logging.info('%s: Not Implemented', 'pimd_bb:show_folder()')

    def del_folder (self, gid, store=None):
        """See the documentation in class PIMDB"""

        if not store:
            logging.error('BBDB:del_folder() needs store to be specified.')
            return

        if not store in self.get_msgstores():
            logging.error('BBDB:del_folder() Could not locate store: %s', store)
            return

        st = self.get_msgstore(store)
        if not gid in st.get_folders():
            logging.error('BBDB:del_folder() Could not locate store: %s', store)
            return

        fold = st.get_folder(gid)
        logging.info('Deleting Entries in folder: %s...', fold.get_name())
        st.remove_folder(fold)
        self.remove_folder(fold)
        logging.info('Deleting Entries in folder: %s...done', fold.get_name())

    def set_folders (self):
        """See the documentation in class PIMDB"""

        for name, store in self.get_msgstores().iteritems():
            for name, f in store.get_folders().iteritems():
                self.add_to_folders(f)

    def set_def_folders (self):
        """See the documentation in class PIMDB"""

        def_store  = self.get_def_msgstore()
        def_folder = def_store.get_folder(MessageStore.get_def_folder_name())
        self.set_def_folder(Folder.CONTACT_t, def_folder)

    def set_sync_folders (self):
        """See the documentation in class PIMDB"""

        raise NotImplementedError

    def prep_for_sync (self, dbid, pname, is_dry_run=False):
        if is_dry_run:
            ## No backup for Dry Run
            logging.info('BBDB database not backed up for dry run')
            return

        conf = self.get_config()
        bdir = os.path.join(conf.get_user_dir(), conf.get_backup_dir())

        if not os.path.exists(bdir):
            logging.info('Creating BBDB backup directory at: %s', bdir)
            os.mkdir(bdir)

        period = conf.get_backup_hold_period()
        logging.info('Deleting BBDB backup files older than %d days, '
                     'if any...', period)
        utils.del_files_older_than(bdir, period)
        logging.info('Deleting BBDB backup files older than %d days, '
                     'if any...done', period)    

        for store in self.get_msgstores().values():
            store.prep_for_sync(pname)

    ##
    ## Now the non-abstract methods and internal methods
    ##

    def _set_regexes_ver6 (self):
        res = {'string' : r'"[^"\\]*(?:\\.[^"\\]*)*"|nil',
               'ws'     : '\s*'}
        re_str_ar = 'nil|\(((' + res['string'] + ')' + res['ws'] + ')*\)'
        res.update({'string_array' : re_str_ar})

        ## Phones
        re_ph_vec = ('\[\s*((?P<phlabel>' + res['string'] + 
                     ')\s*(?P<number>(?P<unstructured>'  +
                     res['string'] + ')|'+
                     '(?P<structured>\d+\s+\d+\s+\d+\s+.+)' +
                     '\s*))\]')
        re_phs = 'nil|(\(\s*(' + re_ph_vec + '\s*)+)\)'
        res.update({'ph_vec' : re_phs})

        ## Addresses
        re_ad_vec = ('\[\s*(?P<adlabel>' + res['string'] + ')\s*(' +
                     '(?P<streets>' + res['string_array'] + ')\s*' +
                     '(?P<city>'    + res['string'] + ')\s*' +
                     '(?P<state>'   + res['string'] + ')\s*' +
                     '(?P<zip>('    + res['string'] + ')|(' + '\d\d\d\d\d))\s*' +
                     '(?P<country>' + res['string'] + ')' +
                     ')\s*\]')
        re_ads = 'nil|\(\s*(' + re_ad_vec + '\s*)+\)'
        res.update({'ad_vec' : re_ads})


        re_note = ('\((?P<field>[^()]+)\s*\.\s*(?P<value>' +
                   res['string'] + '|\d+)+\)')
        re_notes = 'nil|\((' + re_note + '\s*)+\)'
        res.update({'note'  : re_note})
        res.update({'notes' : re_notes})

        ## A full contact entry
        re_con = ('\[\s*' +
                  '(?P<firstname>' + res['string']       + ')\s*' +
                  '(?P<lastname>'  + res['string']       + ')\s*' +
                  '(?P<aka>'       + res['string_array'] + ')\s*' +
                  '(?P<company>'   + res['string']       + ')\s*' +
                  '(?P<phones>'    + res['ph_vec']       + ')\s*' +
                  '(?P<addrs>'     + res['ad_vec']       + ')\s*' +
                  '(?P<emails>'    + res['string_array'] + ')\s*' +
                  '(?P<notes>'     + res['notes']        + ')\s*' +
                  '(?P<cache>'     + res['string']       + ')\s*' +
                  '\s*\]')
        
        ver = '6'

        ## Now save some of the regexes for later use...
        self.add_regexes(ver, {
            'con_re' : re_con,
            'str_re' : res['string'],
            'adr_re' : re_ad_vec,
            'ph_re'  : re_ph_vec,
            'note_re' : res['note'],
            'notes_re' : res['notes'],
            })

    def _set_regexes_ver7 (self, ver='7'):
        res = {'string' : r'"[^"\\]*(?:\\.[^"\\]*)*"|nil',
               'ws'     : '\s*'}
        re_str_ar = 'nil|\(((' + res['string'] + ')' + res['ws'] + ')*\)'
        res.update({'string_array' : re_str_ar})

        ## Phones
        re_ph_vec = ('\[\s*((?P<phlabel>' + res['string'] + 
                     ')\s*(?P<number>(?P<unstructured>'  +
                     res['string'] + ')|'+
                     '(?P<structured>\d+\s+\d+\s+\d+\s+.+)' +
                     '\s*))\]')
        re_phs = 'nil|(\(\s*(' + re_ph_vec + '\s*)+)\)'
        res.update({'ph_vec' : re_phs})

        ## Addresses
        re_ad_vec = ('\[\s*(?P<adlabel>' + res['string'] + ')\s*(' +
                     '(?P<streets>' + res['string_array'] + ')\s*' +
                     '(?P<city>'    + res['string'] + ')\s*' +
                     '(?P<state>'   + res['string'] + ')\s*' +
                     '(?P<zip>('    + res['string'] + ')|(' + '\d\d\d\d\d))\s*' +
                     '(?P<country>' + res['string'] + ')' +
                     ')\s*\]')
        re_ads = 'nil|\(\s*(' + re_ad_vec + '\s*)+\)'
        res.update({'ad_vec' : re_ads})


        re_note = ('\((?P<field>[^()]+)\s*\.\s*(?P<value>' +
                   res['string'] + '|\d+)+\)')
        re_notes = 'nil|\((' + re_note + '\s*)+\)'
        res.update({'note'  : re_note})
        res.update({'notes' : re_notes})

        ## A full contact entry
        re_con = ('\[\s*' +
                  '(?P<firstname>' + res['string']       + ')\s*' +
                  '(?P<lastname>'  + res['string']       + ')\s*' +
                  '(?P<affix>'     + res['string_array'] + ')\s*' +
                  '(?P<aka>'       + res['string_array'] + ')\s*' +
                  '(?P<company>'   + res['string_array'] + ')\s*' +
                  '(?P<phones>'    + res['ph_vec']       + ')\s*' +
                  '(?P<addrs>'     + res['ad_vec']       + ')\s*' +
                  '(?P<emails>'    + res['string_array'] + ')\s*' +
                  '(?P<notes>'     + res['notes']        + ')\s*' +
                  '(?P<cache>'     + res['string']       + ')\s*' +
                  '\s*\]')

        ## Now save some of the regexes for later use...
        self.add_regexes(ver, {
            'con_re' : re_con,
            'str_re' : res['string'],
            'adr_re' : re_ad_vec,
            'ph_re'  : re_ph_vec,
            'note_re' : res['note'],
            'notes_re' : res['notes'],
            })

    ## FIXME: This is an attempt at a gross hack to get quick and
    ## dirty support for v9. Let's see if this works.
    def _set_regexes_ver9 (self, ver='9'):
#        self._set_regexes_ver7(ver='9')

        res = {'string' : r'"[^"\\]*(?:\\.[^"\\]*)*"|nil',
               'ws'     : '\s*'}
        re_str_ar = 'nil|\(((' + res['string'] + ')' + res['ws'] + ')*\)'
        res.update({'string_array' : re_str_ar})

        ## Phones
        re_ph_vec = ('\[\s*((?P<phlabel>' + res['string'] + 
                     ')\s*(?P<number>(?P<unstructured>'  +
                     res['string'] + ')|'+
                     '(?P<structured>\d+\s+\d+\s+\d+\s+.+)' +
                     '\s*))\]')
        re_phs = 'nil|(\(\s*(' + re_ph_vec + '\s*)+)\)'
        res.update({'ph_vec' : re_phs})

        ## Addresses
        re_ad_vec = ('\[\s*(?P<adlabel>' + res['string'] + ')\s*(' +
                     '(?P<streets>' + res['string_array'] + ')\s*' +
                     '(?P<city>'    + res['string'] + ')\s*' +
                     '(?P<state>'   + res['string'] + ')\s*' +
                     '(?P<zip>('    + res['string'] + ')|(' + '\d\d\d\d\d))\s*' +
                     '(?P<country>' + res['string'] + ')' +
                     ')\s*\]')
        re_ads = 'nil|\(\s*(' + re_ad_vec + '\s*)+\)'
        res.update({'ad_vec' : re_ads})


        re_note = ('\((?P<field>[^()]+)\s*\.\s*(?P<value>' +
                   res['string'] + '|\d+)+\)')
        re_notes = 'nil|\((' + re_note + '\s*)+\)'
        res.update({'note'  : re_note})
        res.update({'notes' : re_notes})

        ## A full contact entry
        re_con = ('\[\s*' +
                  '(?P<firstname>' + res['string']       + ')\s*' +
                  '(?P<lastname>'  + res['string']       + ')\s*' +
                  '(?P<affix>'     + res['string_array'] + ')\s*' +
                  '(?P<aka>'       + res['string_array'] + ')\s*' +
                  '(?P<company>'   + res['string_array'] + ')\s*' +
                  '(?P<phones>'    + res['ph_vec']       + ')\s*' +
                  '(?P<addrs>'     + res['ad_vec']       + ')\s*' +
                  '(?P<emails>'    + res['string_array'] + ')\s*' +
                  '(?P<notes>'     + res['notes']        + ')\s*' +
                  '(?P<bbdbid>'    + res['string']       + ')\s*' +
                  '(?P<createdon>' + res['string']   + ')\s*' +
                  '(?P<lastupdated>'  + res['string']   + ')\s*' +
                  '(?P<cache>'     + res['string']       + ')\s*' +
                  '\s*\]')

        ## Now save some of the regexes for later use...
        self.add_regexes(ver, {
            'con_re' : re_con,
            'str_re' : res['string'],
            'adr_re' : re_ad_vec,
            'ph_re'  : re_ph_vec,
            'note_re' : res['note'],
            'notes_re' : res['notes'],
            })

    ##
    ## Now the non-abstract methods and internal methods
    ##

    @classmethod
    def get_bbdb_time (self, t=None):
       """Convert a datetime.datetime object to a time string formatted in the
       bbdb-time-stamp-format of version 7 file format. BBDB timestamps are
       always represented in UTC. So the passed value should either be a naive
       object having the UTC time, or an aware object with tzinfo set."""
    
       # The bbbd ver 7 format uses time stamps in the following format:
       # "%Y-%m-%d %T %z", for e.g. 2012-04-17 09:49:16 +0000. The following
       # code converts a specified time instance (seconds since epoch) to the
       # right format
    
       if not t:
           t = datetime.datetime.utcnow()
       else:
           if t.tzinfo:
               t = t - t.tzinfo.utcoffset(t)
    
       return t.strftime('%Y-%m-%d %H:%M:%S +0000', )

    @classmethod
    def parse_bbdb_time (self, t):
        """Return a datetime object containing naive UTC timestamp based on
        the specified BBDB timestamp string."""

       # IMP: Note that we assume the time is in UTC - and ignore what is
       # actually in the string. This sucks, but this is all I am willing to
       # do for the m moment. FIXME

        res = re.search(r'(\d\d\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d).*', t)
        if res:
            t = res.group(1)
        else:
            return None
        
        return datetime.datetime.strptime(t, '%Y-%m-%d %H:%M:%S')
