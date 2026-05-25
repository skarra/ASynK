# -*- coding: utf-8 -*-
##
## Created : Sat May 24 00:13:00 IST 2026
## SPDX-FileCopyrightText: 2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
#####
##
## Gold tests for the ASynK sync engine using CardDAV <-> BBDB.
## Requires a live CardDAV server — runs best-effort when invoked via
## 'make all', hard error when invoked via 'make sync-cd'.
##
## Usage: python test_sync_cd_bb.py [--url http://host:port/]
##                                  [--user admin]
##                                  [--pass admin]
##                                  [--best-effort]
##

import getopt, logging, os, shutil, sys, time, unittest

## Fix sys.path so we can import asynk modules
CUR_DIR     = os.path.abspath(os.path.dirname(__file__))
DIR_PATH    = os.path.abspath(os.path.join(CUR_DIR, '..', '..'))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk')]
sys.path    = EXTRA_PATHS + sys.path

from state       import Config
from pimdb_bb    import BBPIMDB
from contact_bb  import BBContact
from pimdb_cd    import CDPIMDB
from contact_cd  import CDContact
from sync        import Sync

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------

ASYNK_BASE_DIR = DIR_PATH
USER_DIR       = os.path.abspath(os.path.join(CUR_DIR, 'user_dir'))
STATE_SRC      = os.path.join(DIR_PATH, 'state.init.json')
CONF_SRC       = os.path.join(DIR_PATH, 'config', 'config_v6.json')

BB_FILE        = os.path.abspath(os.path.join(CUR_DIR, 'test_sync_cd_bb.bbdb'))

PROFILE_NAME   = 'testcdbb'

## Module-level state
config      = None
server_url  = 'http://127.0.0.1:5232/'
cd_user     = 'admin'
cd_pass     = 'admin'
best_effort = False

## ---------------------------------------------------------------------------
## Helpers
## ---------------------------------------------------------------------------

def setup_user_dir ():
    if os.path.exists(USER_DIR):
        shutil.rmtree(USER_DIR)
    os.makedirs(USER_DIR)
    shutil.copyfile(STATE_SRC, os.path.join(USER_DIR, 'state.json'))
    shutil.copyfile(CONF_SRC, os.path.join(USER_DIR, 'config.json'))

def create_empty_bbdb (fn):
    with open(fn, 'w', encoding='utf-8') as f:
        f.write(';; -*-coding: utf-8-emacs;-*-\n')
        f.write(';;; file-format: 7\n')

def open_bb (fn):
    db = BBPIMDB(config, fn)
    ms = db.get_def_msgstore()
    f  = ms.get_folder(ms.get_def_folder_name())
    return db, f

def reopen_bb (fn):
    return open_bb(fn)

def open_cd ():
    """Create a CDPIMDB from module-level server_url, cd_user, cd_pass.
    Returns (cddb, cd_folder) where cd_folder is the test addressbook."""
    cddb = CDPIMDB(config, server_url, cd_user, cd_pass)
    return cddb

def create_profile (conf, pname, cd_fid):
    """Create a sync profile for cd<->bb."""
    profile = conf.get_profile_defaults()
    profile.update({
        'coll_1': {'dbid': 'cd', 'stid': server_url, 'foid': cd_fid},
        'coll_2': {'dbid': 'bb', 'stid': BB_FILE, 'foid': 'default'},
        'olgid': None,
        'sync_dir': 'SYNC2WAY',
        'sync_state': None,
        'conflict_resolve': '1',
    })
    conf.add_profile(pname, profile)

def run_sync (conf, pname, cddb, bbdb, dirn=None):
    """Run a sync between CD and BB PIMDBs."""
    startt = conf.get_curr_time()
    sync = Sync(conf, pname, [cddb, bbdb])
    if not dirn:
        dirn = conf.get_sync_dir(pname)
    result = sync.sync(dirn)
    if result:
        conf.set_last_sync_start(pname, val=startt)
        conf.set_last_sync_stop(pname)
        sync.save_item_lists()
    return result

def make_bb_contact (folder, first, last, **kwargs):
    """Create a BBContact with specified fields and add to folder."""
    con = BBContact(folder)
    con.set_firstname(first)
    con.set_lastname(last)
    for key, val in kwargs.items():
        setter = getattr(con, 'set_' + key, None)
        if setter:
            setter(val)
    folder.add_contact(con)
    return con

def create_cd_contact (cd_folder, first, last, email=None):
    """Create a CDContact directly on the CardDAV server."""
    c = CDContact(cd_folder)
    c.set_firstname(first)
    c.set_lastname(last)
    if email:
        c.add_email_home(email)
        c.set_email_prim(email)
    c.save()
    return c

def count_cd_contacts (cd_folder):
    """Return the number of contacts in the CD folder."""
    cd_folder._refresh_contacts()
    return len(cd_folder.get_contacts())

def cleanup_cd_contacts (cd_folder):
    """Delete all contacts in the CD test folder."""
    cd_folder._refresh_contacts()
    itemids = list(cd_folder.get_contacts().keys())
    if itemids:
        cd_folder.del_itemids(itemids)
    cd_folder.reset_contacts()

## ---------------------------------------------------------------------------
## Test Cases
## ---------------------------------------------------------------------------

class TestSyncCDBB(unittest.TestCase):
    """CD <-> BB sync engine integration tests.

    Uses a dedicated CardDAV test addressbook created in setUpClass.
    The BB side uses a temp .bbdb file reset per test.
    """

    @classmethod
    def setUpClass (cls):
        global config

        try:
            cddb = open_cd()
        except Exception as e:
            if best_effort:
                raise unittest.SkipTest(
                    'Could not connect to CardDAV server at %s: %s'
                    % (server_url, e))
            else:
                raise

        ## Create a test addressbook
        test_folder_name = 'asynk_cd_bb_sync_test'
        fo = cddb.new_folder(test_folder_name)
        if fo is None:
            if best_effort:
                raise unittest.SkipTest(
                    'Could not create test addressbook on CardDAV server')
            else:
                raise RuntimeError(
                    'Could not create test addressbook on CardDAV server')

        cls.cddb = cddb
        cls.cd_folder = fo
        cls.test_fid = fo.get_itemid()

        logging.info('Test addressbook ready: %s (%s)',
                     test_folder_name, cls.test_fid)

    @classmethod
    def tearDownClass (cls):
        """Delete all contacts in the test addressbook."""
        cd_folder = getattr(cls, 'cd_folder', None)
        cddb = getattr(cls, 'cddb', None)
        if cd_folder and cddb:
            try:
                cleanup_cd_contacts(cd_folder)
                cddb.del_folder(cd_folder.get_itemid())
            except Exception as e:
                logging.warning('Cleanup failed: %s', e)

    def setUp (self):
        """Fresh BBDB file and clean CD folder for each test."""
        import gc as _gc
        _gc.collect()

        create_empty_bbdb(BB_FILE)
        cleanup_cd_contacts(self.cd_folder)

        ## Reset config from disk to clear stale item lists and profile data
        global config
        setup_user_dir()
        config = Config(asynk_base_dir=ASYNK_BASE_DIR, user_dir=USER_DIR)

        self.cddb.set_config(config)
        self.cd_folder.set_config(config)
        create_profile(config, PROFILE_NAME, self.test_fid)

    def tearDown (self):
        if os.path.exists(BB_FILE):
            os.remove(BB_FILE)

    ## -----------------------------------------------------------------
    ## Test 1: BB -> CD initial sync
    ## -----------------------------------------------------------------

    def test_a_bb_to_cd_initial (self):
        """Create contacts in BB, sync to empty CD. Verify CD has 2."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'SyncAlice', 'BB2CD')
        make_bb_contact(bbf, 'SyncBob', 'BB2CD')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.cddb, bbdb)
        self.assertTrue(result)

        # Verify CD has 2 contacts
        cnt = count_cd_contacts(self.cd_folder)
        self.assertEqual(cnt, 2, 'Expected 2 contacts in CD, got %d' % cnt)

    ## -----------------------------------------------------------------
    ## Test 2: CD -> BB initial sync
    ## -----------------------------------------------------------------

    def test_b_cd_to_bb_initial (self):
        """Create contacts in CD, sync to empty BB."""
        create_cd_contact(self.cd_folder, 'SyncCarol', 'CD2BB',
                          email='carol@test.com')
        create_cd_contact(self.cd_folder, 'SyncDave', 'CD2BB',
                          email='dave@test.com')

        bbdb, bbf = open_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.cddb, bbdb)
        self.assertTrue(result)

        bbdb, bbf = reopen_bb(BB_FILE)
        self.assertEqual(len(bbf.get_contacts()), 2)
        names = sorted([c.get_firstname()
                        for c in bbf.get_contacts().values()])
        self.assertIn('SyncCarol', names)
        self.assertIn('SyncDave', names)

    ## -----------------------------------------------------------------
    ## Test 3: No-op re-sync
    ## -----------------------------------------------------------------

    def test_c_noop_resync (self):
        """After initial sync, a second sync with no changes is a no-op."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'NoOp', 'Test')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.cddb, bbdb)
        self.assertTrue(result)

        # Second sync — should be no-op
        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.cddb, bbdb)
        self.assertTrue(result)

        bbdb, bbf = reopen_bb(BB_FILE)
        self.assertEqual(len(bbf.get_contacts()), 1)

    ## -----------------------------------------------------------------
    ## Test 4: Sync tag persistence
    ## -----------------------------------------------------------------

    def test_d_sync_tags (self):
        """After sync, BB contacts should carry sync tags."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'TagTest', 'CDBB')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.cddb, bbdb)
        self.assertTrue(result)

        bbdb, bbf = reopen_bb(BB_FILE)
        for iid, con in bbf.get_contacts().items():
            tags = con.get_sync_tags()
            self.assertTrue(len(tags) > 0,
                            'BB contact should have sync tags after sync')

    ## -----------------------------------------------------------------
    ## Test 5: Field fidelity
    ## -----------------------------------------------------------------

    def test_e_field_fidelity (self):
        """Create a rich BB contact, sync to CD, verify key fields."""
        bbdb, bbf = open_bb(BB_FILE)
        con = BBContact(bbf)
        con.set_firstname('Fidelity')
        con.set_lastname('CDBBTest')
        con.set_prefix('Dr')
        con.set_nickname('Fiddy')
        con.set_company('TestCorp')
        con.add_email_work('fiddy@work.com')
        con.add_phone_mob(('Mobile', '+1-555-7777'))
        con.add_notes('Important CD-BB note.')
        bbf.add_contact(con)
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.cddb, bbdb)
        self.assertTrue(result)

        # Verify the contact exists in CD
        cnt = count_cd_contacts(self.cd_folder)
        self.assertEqual(cnt, 1)

        # Read the CD contact and check fields
        cons = self.cd_folder.get_contacts()
        cd_con = list(cons.values())[0]
        self.assertEqual(cd_con.get_firstname(), 'Fidelity')
        self.assertEqual(cd_con.get_lastname(), 'CDBBTest')
        self.assertEqual(cd_con.get_company(), 'TestCorp')
        self.assertEqual(cd_con.get_nickname(), 'Fiddy')

    ## -----------------------------------------------------------------
    ## Test 6: Add new contact incrementally
    ## -----------------------------------------------------------------

    def test_f_incremental_add (self):
        """After initial sync, add a new BB contact and re-sync."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'First', 'Batch')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.cddb, bbdb)
        self.assertTrue(result)
        self.assertEqual(count_cd_contacts(self.cd_folder), 1)

        # Add another contact
        bbdb, bbf = reopen_bb(BB_FILE)
        make_bb_contact(bbf, 'Second', 'Batch')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.cddb, bbdb)
        self.assertTrue(result)

        self.assertEqual(count_cd_contacts(self.cd_folder), 2)

    ## -----------------------------------------------------------------
    ## Test 7: Incremental update
    ## -----------------------------------------------------------------

    def test_g_incremental_update (self):
        """After initial sync, modify a BB contact field. Re-sync.
        Verify the CD contact is updated."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'UpdateMe', 'TestCDBB', company='OldCorp')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.cddb, bbdb)
        self.assertTrue(result)
        self.assertEqual(count_cd_contacts(self.cd_folder), 1)

        # Modify the contact in BB
        time.sleep(1.1)  # BBDB timestamp must beat last_sync_stop
        bbdb, bbf = reopen_bb(BB_FILE)
        cons = bbf.find_contacts_by_name(name='UpdateMe')
        self.assertEqual(len(cons), 1)
        cons[0].set_company('NewCorp')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.cddb, bbdb)
        self.assertTrue(result)

        # Verify CD contact has the updated company
        self.cd_folder._refresh_contacts()
        cd_cons = list(self.cd_folder.get_contacts().values())
        self.assertEqual(len(cd_cons), 1)
        self.assertEqual(cd_cons[0].get_company(), 'NewCorp')

    ## -----------------------------------------------------------------
    ## Test 8: Delete propagation
    ## -----------------------------------------------------------------

    def test_h_delete_propagation (self):
        """After initial sync of 2 BB contacts, delete 1 from BB.
        Re-sync. Verify CD has only 1 remaining."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'KeepMe', 'DelTest')
        make_bb_contact(bbf, 'DeleteMe', 'DelTest')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.cddb, bbdb)
        self.assertTrue(result)
        self.assertEqual(count_cd_contacts(self.cd_folder), 2)

        # Delete one contact from BB
        bbdb, bbf = reopen_bb(BB_FILE)
        cons = bbf.find_contacts_by_name(name='DeleteMe')
        self.assertEqual(len(cons), 1)
        bbf.del_itemids([cons[0].get_itemid()])
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.cddb, bbdb)
        self.assertTrue(result)

        # Verify CD now has only 1 contact
        cnt = count_cd_contacts(self.cd_folder)
        self.assertEqual(cnt, 1, 'Expected 1 contact in CD, got %d' % cnt)

        # Verify the right one survived
        cd_cons = list(self.cd_folder.get_contacts().values())
        cd_names = [c.get_firstname() for c in cd_cons]
        self.assertIn('KeepMe', cd_names)
        self.assertNotIn('DeleteMe', cd_names)

    ## -----------------------------------------------------------------
    ## Test 9: Unicode support
    ## -----------------------------------------------------------------

    def test_i_unicode (self):
        """Create BB contacts with Unicode names, sync, verify CD fields."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'Héctor', 'Muñoz')
        make_bb_contact(bbf, '太郎', '山田')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.cddb, bbdb)
        self.assertTrue(result)

        # Verify CardDAV has both with correct names
        self.assertEqual(count_cd_contacts(self.cd_folder), 2)
        cd_cons = list(self.cd_folder.get_contacts().values())
        cd_names = sorted([c.get_firstname() for c in cd_cons])
        self.assertEqual(cd_names, ['Héctor', '太郎'])


## ---------------------------------------------------------------------------
## Main
## ---------------------------------------------------------------------------

def main ():
    global config, server_url, cd_user, cd_pass, best_effort

    try:
        opts, args = getopt.getopt(sys.argv[1:], '',
                                   ['url=', 'user=', 'pass=', 'best-effort'])
    except getopt.error as msg:
        print('Usage: python test_sync_cd_bb.py [--url http://host:port/] '
              '[--user admin] [--pass admin] [--best-effort]')
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
    config = Config(asynk_base_dir=ASYNK_BASE_DIR, user_dir=USER_DIR)

    sys.argv = [sys.argv[0]] + args
    unittest.main(verbosity=2)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    main()
