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
    # tests.new_contact(first='Sahodara', last="Tripati")
    # tests.list_all_contacts()
    # tests.print_contacts(name='Chellam')
    tests.find_items(["AAAcAHNrYXJyYUBhc3luay5vbm1pY3Jvc29mdC5jb20ARgAAAAAA6tvK38NMgEiPrdzycecYvAcACf/6iQHYvUyNzrlQXzUQNgAAAAABDwAACf/6iQHYvUyNzrlQXzUQNgAAHykxIwAA"])
    # tests.clear_folder("AAAcAHNrYXJyYUBhc3luay5vbm1pY3Jvc29mdC5jb20ALgAAAAAA6tvK38NMgEiPrdzycecYvAEACf/6iQHYvUyNzrlQXzUQNgAAEaHqDwAA")

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

    def new_contact (self, first, last):
        con = EXContact(self.cons_f)
        con.set_firstname(first)
        con.set_middlename("Bihari")
        con.set_lastname(last)
        con.set_title("Ex PM")
        con.add_notes("Jolly good fellow")
        con.add_email_work("atal.vajpayee@gov.in")
        con.add_web_home('http://asynk.io')
        con.add_web_home('http://karra-asynk.appspot.com')
        con.add_web_work('http://www.cleartrip.com')
        con.add_web_work('http://www.hackerrank.com')
        con.save()

    def list_all_contacts (self):
        self.cons_f._refresh_items()
        for key, item in self.cons_f.get_items().iteritems():
            print item

    def print_contacts (self, cnt=0, name=None):
        self.cons_f._refresh_items()
        self.cons_f.print_contacts(cnt=cnt, name=name)

    def find_items (self, iids):
        cons = self.cons_f.find_items(iids)

        if cons is None:
            cons = []
        print 'Found %d contacts' % len(cons)

        for con in cons:
            print con

    def clear_folder (self, folder_id):
        fobj, ign = self.ex.find_folder(folder_id)
        fobj.del_all_entries()

    def misc (self):
        self.ex.new_folder("ASynK Contacts 1")
        self.ex.del_folder('AAAcAHNrYXJyYUBhc3luay5vbm1pY3Jvc29mdC5jb20ALgAAAAAA6tvK38NMgEiPrdzycecYvAEACf/6iQHYvUyNzrlQXzUQNgAAEaHsAwAA')


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()
