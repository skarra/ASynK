#!/usr/bin/env python

## Created	 : Tue Jul 19 15:04:46  2011
## Last Modified : Wed Jul 20 12:49:14  2011
##
## Copyright 2011 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
## 

from   state         import Config
from   ol_wrapper    import Outlook, Contact
from   gc_wrapper    import GC
from   win32com.mapi import mapitags

import demjson
import logging

class Sync:
    def __init__ (self, config, fields, ol, gc):
        self.config = config
        self.fields = fields
        self.ol     = ol
        self.gc     = gc


    def reset_state (self):
        """Reset counters and other state information before starting."""
        pass


    def _prep_lists (self):
        self.gc.prep_gc_contact_lists()
        self.ol.prep_ol_contact_lists()


    def _send_new_ol_to_gc (self):
        f = self.gc.new_feed()
        batch_size = 0
        batch_num  = 1
        batch_id   = 'Sync-New-OL-to-GC-%02d' % batch_num

        for olid in self.ol.get_con_new():
            c  = Contact(fields=self.fields, config=self.config,
                         ol=self.ol, entryid=olid, props=None,
                         gcapi=self.gc)
            ce = c.get_gc_entry()
#            print 'ce: ', ce

            f.add_insert(entry=ce, batch_id_string=batch_id)
            batch_size += 1

            if batch_size % 200 == 0:
                # Feeds have to be less than 1MB. We can push this some
                # more
                print 'Batch %02d of New. Feed size: %5.2fK' % (batch_num,
                                                            len(str(f))/1024.0)
                rf = self.gc.exec_batch(f)
                # Check for errors. and status. FIXME
                f = self.gc.new_feed()
                batch_num += 1
                batch_id   = 'Sync-New-OL-to-GC-%02d' % batch_num

    def _get_new_gc_to_ol (self):
        pass

    def _del_ol (self):
        pass

    def _del_gc (self):
        pass

    def _sync_mods(self):
        pass

    def run (self):
        self._prep_lists()

#        self._send_new_ol_to_gc()
#        self._get_new_gc_to_ol()
#        self._del_gc()
#        self._del_ol()
#        self._sync_mods()
        

def get_sync_fields (fn="fields.json"):
    os.chdir(karra_cwd)
    
    fi = None
    try:
        fi = open(fn, "r")
    except IOError, e:
        logging.critical('Error! Could not Open file (%s): %s' % fn, e)
        return

    st = fi.read()
    o = demjson.decode(st)

    ar = []
    for field in o["sync_fields"]:
        try:
            v = getattr(mapitags, field)
            ar.append(v)
        except AttributeError, e:
            logging.error('Field %s not found', field)


    return ar


def main (argv = None):
    logging.getLogger().setLevel(logging.DEBUG)

    fields = get_sync_fields()
    config = Config('app_state.json')
    ol     = Outlook(config)
    gc     = None
    try:
        gc = GC(config, 'karra.etc', 'atlsGL21')
    except gdata.client.BadAuthentication, e:
        logging.critical('Invalid user credentials given: %s',
                         str(e))
        return
    except Exception, e:
        logging.critical('Exception (%s) at login time',
                         str(e))
        return

    sync = Sync(config, fields, ol, gc)
    sync.run()

if __name__ == "__main__":
    main()
