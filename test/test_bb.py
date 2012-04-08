##
## Created       : Sat Apr 07 20:03:04 IST 2012
## Last Modified : Sun Apr 08 08:08:05 IST 2012
##
## Copyright (C) 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
## 

import logging, os, os.path, sys

## Being able to fix the sys.path thusly makes is easy to execute this
## script standalone from IDLE. Hack it is, but what the hell.
DIR_PATH    = os.path.abspath(os.path.dirname(os.path.realpath('../Gout')))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'tools')]
sys.path = EXTRA_PATHS + sys.path

from state         import Config
from pimdb_bb      import BBPIMDB
from folder_bb     import BBContactsFolder
from contact_bb    import BBContact

def main (argv=None):
    print sys.argv

    if len(sys.argv) > 1:
        bbfn = sys.argv[1]
    else:
        bbfn = '/Users/sriramkarra/.bbdb.t'

    tests = TestBBContact(config_fn='../app_state.json',
                          bbfn=bbfn)

class TestBBContact:
    def __init__ (self, config_fn, bbfn):
        logging.debug('Getting started... Reading Config File...')

        self.config = Config(config_fn)
        self.bb     = BBPIMDB(self.config, bbfn)
        self.deff   = self.bb.get_def_folder()

        print "\nHurrah: Name is: ", self.deff.get_name() if self.deff else None

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()
