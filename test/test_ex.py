##
## Created : Mon Mar 31 16:26:27 IST 2014
##
## Copyright (C) 2014 Sriram Karra <karra.etc@gmail.com>
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
## This file is used for some poking around with the EWS code of ASynK -
## stuff like print a contact from a bbdb database, test new changes to pimdb
## or folder code, etc. Essentially some test routines that are not really
## unit tests. code often moves from here to the unittest directory (gold/)
## after a while
##

import logging, os, os.path, sys, traceback

CUR_DIR           = os.path.abspath('')
ASYNK_BASE_DIR    = os.path.abspath('..')
EXTRA_PATHS = [os.path.join(ASYNK_BASE_DIR, 'lib'),
               os.path.join(ASYNK_BASE_DIR, 'asynk'),]
sys.path = EXTRA_PATHS + sys.path

from state         import Config
from pimdb_ex      import EXPIMDB
from contact_ex    import EXContact

def main ():
    ex = init()

def init ():
    tests = TestEXContact(ASYNK_BASE_DIR, './')
    tests.new_contact()

class TestEXContact:
    def __init__ (self, asynk_bd, user_d):
        with open('auth.pwd', 'r') as inf:
            user = inf.readline().strip()
            pw   = inf.readline().strip()
            url  = inf.readline().strip()

        self.conf = Config(asynk_base_dir=asynk_bd, user_dir=user_d)
        self.ex = EXPIMDB(self.conf, user, pw, url)
        self.cons_f = self.ex.get_def_folder()

    def list_folders (self):
        self.ex.list_folders(recursive=False)

    def new_contact (self):
        con = EXContact(self.cons_f)
        con.set_firstname("Atal")
        con.set_middlename("Bihari")
        con.set_lastname("Vajpayee")
        con.set_title("Ex PM")
        con.set_dept("Prime Minister's Office")
        con.set_company("Govt. of India")
        con.save()

    def find_items (self):
        cons = self.conf_f.find_items(['AQAcAHNrYXJyAGFAYXN5bmsub25taWNyb3NvZnQuY29tAEYAAAPq28rfw0yASI+t3PJx5xi8BwAJ//qJAdi9TI3OuVBfNRA2AAACAQ8AAAAJ//qJAdi9TI3OuVBfNRA2AAACEMsAAAA='])

        print 'Found %d contacts' % len(cons)
        for con in cons:
            print con

    def misc (self):
        self.ex.new_folder("ASynK Contacts 1")
        self.ex.del_folder('AAAcAHNrYXJyYUBhc3luay5vbm1pY3Jvc29mdC5jb20ALgAAAAAA6tvK38NMgEiPrdzycecYvAEACf/6iQHYvUyNzrlQXzUQNgAAEaHsAwAA')


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()
