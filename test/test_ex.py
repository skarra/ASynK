##
## Created : Mon Mar 31 16:26:27 IST 2014
## SPDX-FileCopyrightText: 2014-2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
## This file is used for some poking around with the Exchange code of ASynK -
## stuff like print a contact from Exchange, test new changes to pimdb or
## folder code, etc. Essentially some test routines that are not really
## unit tests. Code often moves from here to the unittest directory (gold/)
## after a while.
##
## NOTE: This is a manual integration test that requires a real Azure AD
## app registration and Exchange Online account. For automated unit tests,
## see test/gold/test_msgraph_client.py and
## test/gold/test_contact_field_preservation_ex.py.
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
    # tests.list_folders()
    # tests.new_contact(first='Sahodara', last="Tripati")
    # tests.list_all_contacts()
    # tests.print_contacts(name='Chellam')
    # tests.find_items(["some-graph-contact-id"])
    # tests.clear_folder("some-graph-folder-id")

class TestEXContact:
    def __init__ (self, asynk_bd, user_d):
        """Initialize with Graph API authentication.

        The client_id must be configured in config_v10.json or config.py.
        Authentication uses OAuth 2.0 device code flow — you will be
        prompted to visit a URL and enter a code on the first run.
        """

        self.conf = Config(asynk_base_dir=asynk_bd, user_dir=user_d)
        self.ex = EXPIMDB(self.conf)
        self.cons_f = self.ex.get_def_folder()

    def list_folders (self):
        self.ex.list_folders()

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

        ## Create via Graph API
        client = self.ex.get_graph_client()
        graph_dict = con.to_graph_dict()
        resp = client.create_contact(self.cons_f.get_itemid(), graph_dict)
        print('Created contact with ID:', resp.get('id'))

    def list_all_contacts (self):
        self.cons_f._refresh_items()
        for key, item in self.cons_f.get_items().items():
            print(item)

    def print_contacts (self, cnt=0, name=None):
        self.cons_f._refresh_items()
        self.cons_f.print_contacts(cnt=cnt, name=name)

    def find_items (self, iids):
        cons = self.cons_f.find_items(iids)

        if cons is None:
            cons = []
        print('Found %d contacts' % len(cons))

        for con in cons:
            print(con)

    def clear_folder (self, folder_id):
        fobj, ign = self.ex.find_folder(folder_id)
        fobj.del_all_entries()

    def misc (self):
        self.ex.new_folder("ASynK Contacts 1")


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()
