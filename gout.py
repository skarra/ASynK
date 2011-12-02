##
## Created       : Fri Dec 02 13:46:17 IST 2011
## Last Modified : Fri Dec 02 16:34:21 IST 2011
##
## Copyright (c) 2011 Sriram Karra <karra.etc@gmail.com>
## All Rights Reserved
##
## Licensed under GPLv3
## 

import wx, sys, os, logging, traceback

## First up we need to fix the sys.path before we can even import stuff we
## want... Just some weirdness specific to our code layout...

DIR_PATH    = os.path.abspath(os.path.dirname(os.path.realpath('Gout')))
EXTRA_PATHS = [
    os.path.join(DIR_PATH, 'lib'),
    os.path.join(DIR_PATH, 'tools'),]

sys.path = EXTRA_PATHS + sys.path

## Now life can continue as normal

from   tools.state   import Config
from   ol_wrapper    import Outlook
from   gc_wrapper    import GC
from   sync          import Sync
from   win32com.mapi import mapitags
from   panels        import Panels

import demjson
import gdata.contacts.data
import gdata.contacts.client

class GoutUI:
    def __init__ (self):
        self.sync   = None

        logging.info('Reading app configuration and state...')
        self.config = Config('app_state.json')

        self.ui = Panels(self)

    def get_sync_fields (self, fn="fields.json"):
        os.chdir(DIR_PATH)
        
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
    
        fi.close()
        return ar

    def get_sync_obj (self, user, pwd, dirn):
        logging.info('Opening Outlook message store...')
        ol = Outlook(self.config)
    
        self.fields = self.get_sync_fields()
        self.fields.append(ol.prop_tags.valu('GOUT_PR_EMAIL_1'))
        self.fields.append(ol.prop_tags.valu('GOUT_PR_EMAIL_2'))
        self.fields.append(ol.prop_tags.valu('GOUT_PR_EMAIL_3'))
        self.fields.append(ol.prop_tags.valu('GOUT_PR_GCID'))

        logging.info('Logging into Gmail to set up connection...')
        gc = GC(self.config, user, pwd)
        
        self.sync = Sync(self.config, self.fields, ol, gc, dirn=dirn)    
        return self.sync

    def reset (self, user, pwd, sync_dir):
        try:
            sync = self.get_sync_obj(user, pwd, sync_dir)
            sync._reset_sync()
        except gdata.client.BadAuthentication, e:
            logging.critical('Invalid user credentials given: %s',
                             str(e))
        except Exception, e:
            logging.critical('Exception (%s).', str(e))
            logging.critical(traceback.format_exc())

    def dry_run (self, user, pwd, sync_dir):
        tstr = None
        try:
            sync = self.get_sync_obj(user, pwd, sync_dir)
            sync.dry_run()
        except gdata.client.BadAuthentication, e:
            logging.critical('Invalid user credentials given: %s',
                             str(e))
        except Exception, e:
            logging.critical('Exception (%s).', str(e))
            logging.critical(traceback.format_exc())

    def do_sync (self, user, pwd, sync_dir):
        tstr = None
        try:
            sync = self.get_sync_obj(user, pwd, sync_dir)
            old_sync_start = sync.config.get_last_sync_start()
            new_sync_start = sync.config.get_curr_time()

            sync.run()

            sync.config.set_last_sync_start(val=new_sync_start)
            sync.config.set_last_sync_stop()
        except gdata.client.BadAuthentication, e:
            # Reset the start time so we retry any failed sync
            # attempts. It is theoritically possible to be more granular
            # than this... but this should do for now.
            if tstr:
                sync.config.set_last_sync_start(tstr)
            logging.critical('Invalid user credentials given: %s',
                             str(e))
        except Exception, e:
            logging.critical('Exception (%s).', str(e))
            logging.critical(traceback.format_exc())
        
    def run (self):
        self.ui.run()

def main (argv = None):
    logging.getLogger().setLevel(logging.DEBUG)

    gui = GoutUI()
    gui.run()


if __name__ == "__main__":
    main()
