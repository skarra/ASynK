##
## Created       : Mon Apr 09 14:54:10 IST 2012
## Last Modified : Mon Apr 09 17:26:08 IST 2012
##
## Copyright (C) 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
## 

import logging, os, os.path, sys, traceback

## Being able to fix the sys.path thusly makes is easy to execute this
## script standalone from IDLE. Hack it is, but what the hell.
DIR_PATH    = os.path.abspath(os.path.dirname(os.path.realpath('../Gout')))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'tools')]
sys.path = EXTRA_PATHS + sys.path


import base64
from   sync       import SyncLists
from   state      import Config
from   pimdb_ol   import OLPIMDB
from   contact_ol import OLContact

def main (argv=None):
    tests = TestOLContact()
    
    tests.print_contact('AAAAADWE5+lnNclLmn8GpZUD04fE7C0A')

    # tests.test_read_emails('AAAAADWE5+lnNclLmn8GpZUD04fE7C0A')
    # tests.test_new_contact()
    # tests.test_sync_status()

class TestOLContact:
    def __init__ (self):
        logging.debug('Getting started... Reading Config File...')

        self.config = Config('../app_state.json')
        self.ol     = OLPIMDB(self.config)
        self.deff   = self.ol.get_def_folder()

        print "\nHurrah: Name is: ", self.deff.get_name()

    def print_contact (self, itemid):
        eid = base64.b64decode(itemid)
        c = OLContact(self.deff, eid=eid)
        logging.debug('Contact: \n%s', str(c))        

    def test_new_contact (self):
        c = OLContact(self.deff)
        c.set_name('Supeman')
        c.set_gender('Male')
        c.set_notes('This is a second test contact')
        c.save()

    def test_read_emails (self, itemid):
        eid = base64.b64decode(itemid)
        olcf = self.deff
        
        prop_tag = olcf.get_proptags().valu('ASYNK_PR_EMAIL_1')
        store    = olcf.get_msgstore()
        item     = store.get_obj().OpenEntry(eid, None, mapi.MAPI_BEST_ACCESS)

        hr, props = item.GetProps([prop_tag], mapi.MAPI_UNICODE)
        (tag, val) = props[0]
        if mt.PROP_TYPE(tag) == mt.PT_ERROR:
            print 'Prop_Tag (0x%16x) not found. Tag: 0x%16x' % (prop_tag,
                                                                (tag % (2**64)))
        else:
            print 'Email address found: ', val

    def test_sync_status (self):
        sl = SyncLists(self.deff, 'gc')
        self.deff.prep_sync_lists('gc', sl)

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    try:
        main()
    except Exception, e:
        print 'Caught Exception... Hm. Need to cleanup.'
        print 'Full Exception as here:', traceback.format_exc()

## FIXME: Needs more thorough unit testing.
