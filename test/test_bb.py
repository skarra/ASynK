##
## Created : Sat Apr 07 20:03:04 IST 2012
## SPDX-FileCopyrightText: 2012-2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
## This file is used for some poking around with the BBDB code of ASynK -
## stuff like print a contact from a bbdb database, test new changes to pimdb
## or folder code, etc. Essentially some test routines that are not really
## unit tests. code often moves from here to the unittest directory (gold/)
## after a while

## You can use this to quickly check if ASynK can parse your bbdb file. Usage:
## python test_bb.py <bbdb_file>

import logging, os, os.path, sys, traceback

## Being able to fix the sys.path thusly makes is easy to execute this
## script standalone from IDLE. Hack it is, but what the hell.
CUR_DIR           = os.path.abspath('')
ASYNK_BASE_DIR    = os.path.abspath('..')
print(ASYNK_BASE_DIR)
EXTRA_PATHS = [os.path.join(ASYNK_BASE_DIR, 'lib'),
               os.path.join(ASYNK_BASE_DIR, 'asynk'),]
sys.path = EXTRA_PATHS + sys.path

from state         import Config
from pimdb_bb      import BBPIMDB
from folder_bb     import BBContactsFolder
from contact_bb    import BBContact

def main (argv=None):
    print(sys.argv)

    if len(sys.argv) > 1:
        bbfn = os.path.abspath(sys.argv[1])
    else:
        bbfn = '/Users/sriramkarra/.bbdb.t'

    tests = TestBBContact(asynk_base_dir=ASYNK_BASE_DIR, user_dir='./',
                          bbfn=bbfn)
    if len(sys.argv) > 2:
        name = sys.argv[2]
    else:
        name = None

    tests.print_contacts(name=name)
    # tests.write_to_file()

class TestBBContact:
    def __init__ (self, asynk_base_dir, user_dir, bbfn):
        logging.debug('Getting started... Reading Config File...')

        self.config = Config(asynk_base_dir, user_dir)
        self.bb     = BBPIMDB(self.config, bbfn)
        ms          = self.bb.get_def_msgstore()
        self.deff   = ms.get_folder(ms.get_def_folder_name())

    def print_contacts (self, cnt=0, name=None):
        self.deff.print_contacts(cnt=cnt, name=name)

    def write_to_file (self):
        self.deff.save()

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()
