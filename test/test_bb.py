##
## Created       : Sat Apr 07 20:03:04 IST 2012
## Last Modified : Wed Apr 18 06:05:42 IST 2012
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

    tests = TestBBContact(config_fn='../config.json',
                          state_fn='../state.json',
                          bbfn=bbfn)
    tests.print_contacts(cnt=1)
    # tests.write_to_file()

class TestBBContact:
    def __init__ (self, config_fn, state_fn, bbfn):
        logging.debug('Getting started... Reading Config File...')

        self.config = Config(config_fn, state_fn)
        self.bb     = BBPIMDB(self.config, bbfn)
        self.deff   = self.bb.get_def_folder()

    def print_contacts (self, cnt):
        self.deff.print_contacts(cnt=cnt)

    def write_to_file (self):
        self.deff.save_file()

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()
