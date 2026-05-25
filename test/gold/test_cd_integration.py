##
## Created : Sat May 23 2026
## SPDX-FileCopyrightText: 2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK

import getopt, logging, os, os.path, shutil, sys, unittest, time

## Fix sys.path so we can import asynk modules
DIR_PATH    = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath('__file__')), '../..'))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk')]
sys.path = EXTRA_PATHS + sys.path

from state    import Config
from pimdb_cd import CDPIMDB
from contact_cd import CDContact

## Directories
user_dir     = os.path.abspath('user_dir')
state_src    = os.path.join('.', 'state.test.json')
state_dest   = os.path.join(user_dir, 'state.json')
confn_src    = os.path.join('..', '..', 'config', 'config_v4.json')
confn_dest   = os.path.join(user_dir, 'config.json')

## Options
config    = None
server_url = "http://127.0.0.1:5232/"
cd_user   = "admin"
cd_pass   = "admin"
best_effort = False

def setup_user_dir ():
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)
    os.makedirs(user_dir)
    shutil.copyfile(state_src, state_dest)
    if os.path.exists(confn_src):
        shutil.copyfile(confn_src, confn_dest)

def print_suite_banner(suite_name):
    print('\n' + '='*80)
    print('>>> INITIALIZING TEST SUITE: %s' % suite_name)
    print('='*80)

def print_test_banner(test_name):
    print('\n' + '-'*80)
    print('>> RUNNING TEST: %s' % test_name)
    print('-'*80)

class TestCDAuth(unittest.TestCase):
    @classmethod
    def setUpClass (cls):
        print_suite_banner(cls.__name__)
        try:
            cls.pimdb = CDPIMDB(config, server_url, cd_user, cd_pass)
        except Exception as e:
            if best_effort:
                raise unittest.SkipTest("CardDAV server not reachable: %s" % e)
            raise

    def setUp (self):
        print_test_banner(self._testMethodName)

    def test_dbid (self):
        self.assertEqual(self.pimdb.get_dbid(), 'cd')

    def test_user (self):
        self.assertEqual(self.pimdb.get_user(), cd_user)


class TestCDFolders(unittest.TestCase):
    @classmethod
    def setUpClass (cls):
        print_suite_banner(cls.__name__)
        try:
            cls.pimdb = CDPIMDB(config, server_url, cd_user, cd_pass)
        except Exception as e:
            if best_effort:
                raise unittest.SkipTest("CardDAV server not reachable: %s" % e)
            raise

    def setUp (self):
        print_test_banner(self._testMethodName)

    def test_list_folders (self):
        folders = self.pimdb.list_folders(silent=True)
        self.assertIsInstance(folders, list)
        self.assertGreater(len(folders), 0)

    def test_create_and_delete_folder (self):
        test_name = 'asynk_test_adbk'
        
        # Create
        fo = self.pimdb.new_folder(test_name)
        self.assertIsNotNone(fo)
        self.assertEqual(fo.get_name(), test_name)
        
        # Verify it's listed
        folders = self.pimdb.list_folders(silent=True)
        found = False
        for f in folders:
            if f[1] == test_name:
                found = True
                break
        self.assertTrue(found)
        
        # Delete
        self.pimdb.del_folder(fo.get_itemid())


class TestCDContacts(unittest.TestCase):
    @classmethod
    def setUpClass (cls):
        print_suite_banner(cls.__name__)
        try:
            cls.pimdb = CDPIMDB(config, server_url, cd_user, cd_pass)
        except Exception as e:
            if best_effort:
                raise unittest.SkipTest("CardDAV server not reachable: %s" % e)
            raise
        
        # Create temporary addressbook
        cls.test_folder = cls.pimdb.new_folder('cd_integration_tests')
        assert cls.test_folder is not None

    @classmethod
    def tearDownClass (cls):
        if hasattr(cls, 'test_folder') and cls.test_folder is not None:
            cls.pimdb.del_folder(cls.test_folder.get_itemid())

    def setUp (self):
        print_test_banner(self._testMethodName)

    def test_a_empty_folder (self):
        # Refresh and list contacts should be empty
        self.test_folder._refresh_contacts()
        self.assertEqual(len(self.test_folder.get_contacts()), 0)

    def test_b_create_and_read_contact (self):
        c = CDContact(self.test_folder)
        c.set_firstname('Radicale')
        c.set_lastname('Test')
        c.set_prefix('Dr.')
        c.add_email_home('radicale@example.com')
        c.set_email_prim('radicale@example.com')
        
        # Save to server
        success = c.save()
        self.assertTrue(success)
        self.assertIsNotNone(c.get_itemid())
        
        # Read it back using find_item
        fetched = self.test_folder.find_item(c.get_itemid())
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.get_firstname(), 'Radicale')
        self.assertEqual(fetched.get_lastname(), 'Test')
        self.assertEqual(fetched.get_email_prim(), 'radicale@example.com')
        
        self.__class__._created_itemid = c.get_itemid()

    def test_c_update_contact (self):
        itemid = getattr(self.__class__, '_created_itemid', None)
        if not itemid:
            self.skipTest("No contact created")
            
        fetched = self.test_folder.find_item(itemid)
        self.assertIsNotNone(fetched)
        
        fetched.set_firstname('RadicaleUpdated')
        fetched.save(etag=fetched.get_etag())
        
        # Read back and verify
        updated = self.test_folder.find_item(itemid)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.get_firstname(), 'RadicaleUpdated')

    def test_d_find_items_multiget (self):
        itemid = getattr(self.__class__, '_created_itemid', None)
        if not itemid:
            self.skipTest("No contact created")
            
        # Bulk multiget
        contacts = self.test_folder.find_items([itemid])
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0].get_firstname(), 'RadicaleUpdated')
        self.assertIsNotNone(contacts[0].get_etag())

    def test_e_delete_contact (self):
        itemid = getattr(self.__class__, '_created_itemid', None)
        if not itemid:
            self.skipTest("No contact created")
            
        self.test_folder.del_itemids([itemid])
        
        # Verify it's gone
        fetched = self.test_folder.find_item(itemid)
        self.assertIsNone(fetched)


def main ():
    global config, server_url, cd_user, cd_pass, best_effort

    try:
        opts, args = getopt.getopt(sys.argv[1:], '',
                                   ['url=', 'user=', 'pass=', 'best-effort'])
    except getopt.error as msg:
        print('Usage: python test_cd_integration.py [--url server_url] [--user user] [--pass pass] [--best-effort]')
        sys.exit(2)

    for option, arg in opts:
        if option == '--url':
            server_url = arg
        elif option == '--user':
            cd_user = arg
        elif option == '--pass':
            cd_pass = arg
        elif option == '--best-effort':
            best_effort = True

    setup_user_dir()
    config = Config(asynk_base_dir='../../', user_dir=user_dir)

    # Clean custom arguments
    sys.argv = [sys.argv[0]]
    unittest.main(verbosity=2)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    main()
