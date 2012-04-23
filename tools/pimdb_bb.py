##
## Created       : Sat Apr 07 18:52:19 IST 2012
## Last Modified : Mon Apr 23 15:30:46 IST 2012
##
## Copyright (C) 2012 by Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
##

import logging, re, time, datetime
from   pimdb        import PIMDB
from   folder       import Folder
from   folder_bb    import BBContactsFolder

class BBPIMDB(PIMDB):
    """Wrapper class over the BBDB, by implementing the PIMDB abstract
    class."""

    def __init__ (self, config, def_fn):
        PIMDB.__init__(self, config)

        self.set_def_fn(def_fn)
        self._set_regexes()
        self.set_folders()

    ##
    ## First implementation of the abstract methods of PIMDB.
    ##

    def get_dbid (self):
        """See the documentation in class PIMDB"""

        return 'bb'

    def list_folders (self):
        """See the documentation in class PIMDB"""

        ## BBDB is intended to be a one database system...
        logging.info('  %2d; Name: %-32s ID: %s', 1, self.get_def_fn(),
                     None)

    def new_folder (self, fname, ftype=None, storeid=None):
        """See the documentation in class PIMDB.

        fname should be a filename in this case.
        """

        with open(fname, 'w') as bbf:
            bbf.write(';; -*-coding: utf-8-emacs;-*-\n')
            bbf.write(';;; file-format: 8\n')
            bbf.write(';;; user-fields: \n')
            bbf.close()

        logging.info('Successfully Created BBDB file: %s', fname)

    def del_folder (self, gid):
        """See the documentation in class PIMDB"""

        raise NotImplementedError

    def set_folders (self):
        """See the documentation in class PIMDB"""

        f = BBContactsFolder(self, self.get_def_fn())
        if f:
            self.add_contacts_folder(f)
            self.set_def_folder(Folder.CONTACT_t, f)

    def set_def_folders (self):
        """See the documentation in class PIMDB"""

        ## We are already doing the needful above...
        pass

    def set_sync_folders (self):
        """See the documentation in class PIMDB"""

        raise NotImplementedError

    def prep_for_sync (self, dbid):
        pass

    ##
    ## Now the non-abstract methods and internal methods
    ##


    def get_def_fn (self):
        return self._get_att('def_fn')

    def set_def_fn (self, fn):
        return self._set_att('def_fn', fn)

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

    def _set_regexes (self):
        res = {'string' : r'"[^"\\]*(?:\\.[^"\\]*)*"|nil',
               'ws'     : '\s*'}
        re_str_ar = 'nil|\(((' + res['string'] + ')' + res['ws'] + ')*\)'
        res.update({'string_array' : re_str_ar})

        ## Phones
        re_ph_vec = ('\[\s*((?P<phlabel>' + res['string'] + 
                     ')\s*(?P<number>(?P<unstructured>'  +
                     res['string'] + ')|'+
                     '(?P<structured>\d+\s+\d+\s+\d+\s+\d+)' +
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
        re_notes = '\((' + re_note + '\s*)+\)'
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
        self.set_con_re(re_con)
        self.set_str_re(res['string'])
        self.set_adr_re(re_ad_vec)
        self.set_ph_re(re_ph_vec)
        self.set_note_re(res['note'])
        self.set_notes_re(res['notes'])

        # Compute and store away a regular expression to match sync tags in
        # the notes section
        c = self.get_config()
        p = c.get_label_prefix()
        s = c.get_label_separator()
        r = '%s%s\w+%s' % (p, s, s)
        self.set_sync_tag_re(r)
        
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
