# -*- coding: utf-8 -*-
##
## Created : Tue May 26 18:25:00 PDT 2026
## SPDX-FileCopyrightText: 2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
## ####
##
## Gold tests for the ASynK sync engine using Exchange Online <-> BBDB.
## Requires live Exchange credentials (Azure AD app client ID) — runs best-effort
## when invoked via 'make all', hard error when invoked via 'make sync-ex-bb'.
##
## Usage: python test_sync_ex_bb.py [--client-id YOUR-CLIENT-ID]
##                                  [--tenant-id TENANT]
##                                  [--best-effort]
##

import getopt, logging, os, shutil, sys, time, unittest
import demjson3 as demjson

## Fix sys.path so we can import asynk modules
CUR_DIR     = os.path.abspath(os.path.dirname(__file__))
DIR_PATH    = os.path.abspath(os.path.join(CUR_DIR, '..', '..'))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk')]
sys.path    = EXTRA_PATHS + sys.path

from state       import Config
from pimdb_ex    import EXPIMDB
from pimdb_bb    import BBPIMDB
from contact_bb  import BBContact
from contact_ex  import EXContact, ASYNK_EXTENSION_NAME
from sync        import Sync

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------

ASYNK_BASE_DIR = DIR_PATH
USER_DIR       = os.path.abspath(os.path.join(CUR_DIR, 'user_dir'))
STATE_SRC      = os.path.join(DIR_PATH, 'state.init.json')
CONF_SRC       = os.path.join(DIR_PATH, 'config', 'config_v10.json')

EX_CREDS_DIR   = os.path.abspath(os.path.join(CUR_DIR, 'ex_creds'))
BB_FILE        = os.path.abspath(os.path.join(CUR_DIR, 'test_sync_ex_bb.bbdb'))

PROFILE_NAME   = 'testexbb'
TEST_GROUP     = 'ASynK Sync Test (safe to delete)'

## Module-level state
config             = None
resolved_client_id = None
resolved_tenant_id = None
token_cache        = None

## ---------------------------------------------------------------------------
## Helpers
## ---------------------------------------------------------------------------

def print_suite_banner(suite_name):
    print('\n' + '='*80)
    print('>>> INITIALIZING TEST SUITE: %s' % suite_name)
    print('='*80)

def print_test_banner(test_name):
    print('\n' + '-'*80)
    print('>> RUNNING TEST: %s' % test_name)
    print('-'*80)

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

def create_profile (conf, pname, ex_fid):
    """Create a sync profile for ex<->bb."""
    profile = conf.get_profile_defaults()
    profile.update({
        'coll_1': {'dbid': 'ex', 'stid': None, 'foid': ex_fid},
        'coll_2': {'dbid': 'bb', 'stid': BB_FILE, 'foid': 'default'},
        'olgid': None,
        'sync_dir': 'SYNC2WAY',
        'sync_state': None,
        'conflict_resolve': '1',
    })
    conf.add_profile(pname, profile)

def run_sync (conf, pname, exdb, bbdb, dirn=None):
    """Run a sync between Exchange and BB PIMDBs."""
    startt = conf.get_curr_time()
    sync = Sync(conf, pname, [exdb, bbdb])
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

def create_ex_contact (exdb, fid, first, last, email=None, phone=None):
    """Create a contact directly in Exchange and return the ID."""
    client = exdb.get_graph_client()
    contact = {
        'givenName': first,
        'surname': last,
    }
    if email:
        contact['emailAddresses'] = [{'address': email, 'name': 'Work Email'}]
    if phone:
        contact['mobilePhone'] = phone

    resp = client.create_contact(fid, contact)
    return resp.get('id')

def delete_ex_contact (exdb, cid):
    """Delete a contact from Exchange by ID."""
    client = exdb.get_graph_client()
    client.delete_contact(cid)

def update_ex_contact_company (exdb, cid, company):
    """Update the company/organization of an Exchange contact."""
    client = exdb.get_graph_client()
    client.update_contact(cid, {'companyName': company})

def count_ex_contacts (ex_folder):
    """Return the number of contacts in the EX folder."""
    ex_folder._refresh_items()
    return len(ex_folder.get_contacts())

def cleanup_ex_contacts (ex_folder, exdb):
    """Delete all contacts in the EX test folder."""
    ex_folder.del_all_entries()

## ---------------------------------------------------------------------------
## Test Cases
## ---------------------------------------------------------------------------

class TestSyncEXBB(unittest.TestCase):
    """Exchange <-> BB sync engine integration tests."""

    @classmethod
    def setUpClass (cls):
        print_suite_banner(cls.__name__)
        if not resolved_client_id:
            raise unittest.SkipTest(
                'No client-id available; skipping EX sync tests.')

        try:
            cls.exdb = EXPIMDB(config, client_id=resolved_client_id,
                               tenant_id=resolved_tenant_id,
                               token_cache_path=token_cache)
        except Exception as e:
            logging.warning('Skipping test suite due to EXPIMDB init failure: %s', e)
            raise unittest.SkipTest('Exchange auth/connection failed')

        ## Try to create or find our dedicated test group/folder
        cls.test_gid = None
        try:
            res = cls.exdb.new_folder(TEST_GROUP)
            if res:
                cls.test_gid = res.get('id')
        except Exception:
            pass

        # Force reload folders from the server so the new folder is registered locally
        cls.exdb.folders = {'contacts':[],'tasks':[],'notes':[],'appts':[],}
        cls.exdb.set_folders()

        if cls.test_gid is None:
            # Look for existing folder with same name
            for f in cls.exdb.get_contacts_folders():
                if f.get_name() == TEST_GROUP:
                    cls.test_gid = f.get_itemid()
                    break

        if cls.test_gid is None:
            raise unittest.SkipTest('Could not create or find Exchange test folder')

        cls.ex_folder = None
        for f in cls.exdb.get_contacts_folders():
            if f.get_itemid() == cls.test_gid:
                cls.ex_folder = f
                break

        if cls.ex_folder is None:
            raise unittest.SkipTest('Could not locate Exchange test folder')

        create_profile(config, PROFILE_NAME, cls.test_gid)

    @classmethod
    def tearDownClass (cls):
        """Delete the test folder and all contacts in it."""
        fid = getattr(cls, 'test_gid', None)
        if fid and hasattr(cls, 'exdb'):
            try:
                cleanup_ex_contacts(cls.ex_folder, cls.exdb)
                time.sleep(1)
                cls.exdb.del_folder(fid)
            except Exception as e:
                logging.warning('Cleanup failed: %s', e)
        time.sleep(2)

    def setUp (self):
        """Fresh BBDB file for each test. Reset EX test folder."""
        import gc as _gc
        _gc.collect()

        print_test_banner(self._testMethodName)

        create_empty_bbdb(BB_FILE)
        cleanup_ex_contacts(self.ex_folder, self.exdb)
        self.ex_folder.reset_contacts()
        time.sleep(2)  # Let server-side operations settle

        ## Reset state.json within EX_CREDS_DIR to clear stale item lists
        shutil.copyfile(STATE_SRC, os.path.join(EX_CREDS_DIR, 'state.json'))

        global config
        config = Config(asynk_base_dir=ASYNK_BASE_DIR, user_dir=EX_CREDS_DIR)

        self.exdb.set_config(config)
        self.ex_folder.set_config(config)
        create_profile(config, PROFILE_NAME, self.test_gid)

    def tearDown (self):
        if os.path.exists(BB_FILE):
            os.remove(BB_FILE)

    ## -----------------------------------------------------------------
    ## Test 1: BB -> EX initial sync
    ## -----------------------------------------------------------------

    def test_a_bb_to_ex_initial (self):
        """Create contacts in BB, sync to empty Exchange group."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'SyncAlice', 'BB2EX')
        make_bb_contact(bbf, 'SyncBob', 'BB2EX')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)

        cnt = count_ex_contacts(self.ex_folder)
        self.assertEqual(cnt, 2, 'Expected 2 contacts in EX, got %d' % cnt)

    ## -----------------------------------------------------------------
    ## Test 2: EX -> BB initial sync
    ## -----------------------------------------------------------------

    def test_b_ex_to_bb_initial (self):
        """Create contacts in Exchange directly, sync to empty BBDB."""
        create_ex_contact(self.exdb, self.test_gid,
                          'SyncCarol', 'EX2BB', email='carol@test.com')
        create_ex_contact(self.exdb, self.test_gid,
                          'SyncDave', 'EX2BB', phone='+1-555-9999')
        time.sleep(2)

        bbdb, bbf = open_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
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
        create_ex_contact(self.exdb, self.test_gid, 'NoOp', 'Test')
        time.sleep(2)

        bbdb, bbf = open_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)

        # Second sync - should be a no-op
        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)

        bbdb, bbf = reopen_bb(BB_FILE)
        self.assertEqual(len(bbf.get_contacts()), 1)

    ## -----------------------------------------------------------------
    ## Test 4: Sync tag persistence
    ## -----------------------------------------------------------------

    def test_d_sync_tags (self):
        """After sync, BB contacts should carry sync tags."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'TagTest', 'EXBB')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
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
        """Create a rich BB contact, sync to EX, verify key fields."""
        bbdb, bbf = open_bb(BB_FILE)
        con = BBContact(bbf)
        con.set_firstname('Fidelity')
        con.set_lastname('EXBBTest')
        con.set_prefix('Dr')
        con.set_nickname('Fiddy')
        con.set_company('TestCorp')
        con.add_email_work('fiddy@work.com')
        con.add_phone_mob(('Mobile', '+1-555-7777'))
        con.add_notes('Important EX-BB note.')
        bbf.add_contact(con)
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)

        # Verify contact in EX
        self.ex_folder._refresh_items()
        contacts = list(self.ex_folder.get_contacts().values())
        self.assertEqual(len(contacts), 1)
        exc = contacts[0]

        self.assertEqual(exc.get_firstname(), 'Fidelity')
        self.assertEqual(exc.get_lastname(), 'EXBBTest')
        self.assertEqual(exc.get_company(), 'TestCorp')
        self.assertEqual(exc.get_prefix(), 'Dr')
        self.assertEqual(exc.get_nickname(), 'Fiddy')

    ## -----------------------------------------------------------------
    ## Test 6: Add new contact incrementally
    ## -----------------------------------------------------------------

    def test_f_incremental_add (self):
        """After initial sync, add a new BB contact and re-sync."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'First', 'Batch')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)
        self.assertEqual(count_ex_contacts(self.ex_folder), 1)

        # Add another contact
        bbdb, bbf = reopen_bb(BB_FILE)
        make_bb_contact(bbf, 'Second', 'Batch')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)

        self.assertEqual(count_ex_contacts(self.ex_folder), 2)

    ## -----------------------------------------------------------------
    ## Test 7: Batch chunking
    ## -----------------------------------------------------------------

    def test_g_batch_chunking (self):
        """Sync enough contacts to trigger multiple API batches."""
        from folder_ex import EXFolder
        orig_batch = EXFolder.get_batch_size
        # Temporarily mock batch size to 1
        EXFolder.get_batch_size = lambda self: 1
        try:
            N = 3
            bbdb, bbf = open_bb(BB_FILE)
            for i in range(N):
                make_bb_contact(bbf, 'Chunk%02d' % i, 'Test')
            bbf.save()

            bbdb, bbf = reopen_bb(BB_FILE)
            result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
            self.assertTrue(result)

            cnt = count_ex_contacts(self.ex_folder)
            self.assertEqual(cnt, N,
                             'Expected %d contacts in EX, got %d' % (N, cnt))
        finally:
            EXFolder.get_batch_size = orig_batch

    ## -----------------------------------------------------------------
    ## Test 8: Incremental update
    ## -----------------------------------------------------------------

    def test_h_incremental_update (self):
        """After initial sync, modify a BB contact field. Re-sync and verify EX updated."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'UpdateMe', 'TestEXBB', company='OldCorp')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)
        self.assertEqual(count_ex_contacts(self.ex_folder), 1)

        time.sleep(1.1)
        bbdb, bbf = reopen_bb(BB_FILE)
        cons = bbf.find_contacts_by_name(name='UpdateMe')
        self.assertEqual(len(cons), 1)
        cons[0].set_company('NewCorp')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)

        self.ex_folder._refresh_items()
        contacts = list(self.ex_folder.get_contacts().values())
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0].get_company(), 'NewCorp')

    ## -----------------------------------------------------------------
    ## Test 9: Delete propagation
    ## -----------------------------------------------------------------

    def test_i_delete_propagation (self):
        """After initial sync of 2 contacts, delete 1 from BB. Re-sync and verify EX has only 1."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'KeepMe', 'DelTest')
        make_bb_contact(bbf, 'DeleteMe', 'DelTest')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)
        self.assertEqual(count_ex_contacts(self.ex_folder), 2)

        # Delete one from BB
        bbdb, bbf = reopen_bb(BB_FILE)
        cons = bbf.find_contacts_by_name(name='DeleteMe')
        self.assertEqual(len(cons), 1)
        bbf.del_itemids([cons[0].get_itemid()])
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)

        time.sleep(1)
        cnt = count_ex_contacts(self.ex_folder)
        self.assertEqual(cnt, 1, 'Expected 1 contact in EX, got %d' % cnt)

        self.ex_folder._refresh_items()
        names = [c.get_firstname() for c in self.ex_folder.get_contacts().values()]
        self.assertIn('KeepMe', names)
        self.assertNotIn('DeleteMe', names)

    ## -----------------------------------------------------------------
    ## Test 10: One-Way Sync Basic
    ## -----------------------------------------------------------------

    def test_j_sync1way_basic (self):
        """Create a contact in EX, sync 1-way. Verify it appears in BBDB."""
        config.set_sync_dir(PROFILE_NAME, 'SYNC1WAY')

        create_ex_contact(self.exdb, self.test_gid,
                          'OneWayEX', 'Test', email='oneway@test.com')
        time.sleep(2)

        bbdb, bbf = open_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)

        bbdb, bbf = reopen_bb(BB_FILE)
        self.assertEqual(len(bbf.get_contacts()), 1)
        names = [c.get_firstname() for c in bbf.get_contacts().values()]
        self.assertIn('OneWayEX', names)

    ## -----------------------------------------------------------------
    ## Test 11: One-Way Sync Ignores Destination Changes
    ## -----------------------------------------------------------------

    def test_k_sync1way_ignores_dst_changes (self):
        """After 1-way sync, add contact in BBDB. Re-sync and verify EX is unchanged."""
        config.set_sync_dir(PROFILE_NAME, 'SYNC1WAY')

        create_ex_contact(self.exdb, self.test_gid, 'OneWayEX', 'Test')
        time.sleep(2)

        bbdb, bbf = open_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)

        # Add new contact to destination
        bbdb, bbf = reopen_bb(BB_FILE)
        make_bb_contact(bbf, 'BBOnly', 'Contact')
        bbf.save()

        # Re-sync 1-way
        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)

        self.assertEqual(count_ex_contacts(self.ex_folder), 1)

    ## -----------------------------------------------------------------
    ## Test 12: Conflict Resolution - EX Wins
    ## -----------------------------------------------------------------

    def test_l_conflict_ex_wins (self):
        """Modify the same contact on both sides. EX (DB1) wins."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'ConflictMe', 'TestEXBB', company='OldCorp')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)
        self.assertEqual(count_ex_contacts(self.ex_folder), 1)

        self.ex_folder._refresh_items()
        contacts = list(self.ex_folder.get_contacts().values())
        self.assertEqual(len(contacts), 1)
        cid = contacts[0].get_itemid()

        time.sleep(8.0)  # Beat last sync timestamp clock skew tolerance

        bbdb, bbf = reopen_bb(BB_FILE)
        cons = bbf.find_contacts_by_name(name='ConflictMe')
        self.assertEqual(len(cons), 1)
        cons[0].set_company('BBDBCorp')
        bbf.save()

        update_ex_contact_company(self.exdb, cid, 'EXCorp')

        config.set_conflict_resolve(PROFILE_NAME, '1')

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)

        # Verify BBDB updated to 'EXCorp'
        bbdb, bbf = reopen_bb(BB_FILE)
        cons = bbf.find_contacts_by_name(name='ConflictMe')
        self.assertEqual(len(cons), 1)
        self.assertEqual(cons[0].get_company(), 'EXCorp')

    ## -----------------------------------------------------------------
    ## Test 13: Conflict Resolution - BB Wins
    ## -----------------------------------------------------------------

    def test_m_conflict_bb_wins (self):
        """Modify the same contact on both sides. BB (DB2) wins."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'ConflictMe', 'TestEXBB', company='OldCorp')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)
        self.assertEqual(count_ex_contacts(self.ex_folder), 1)

        self.ex_folder._refresh_items()
        contacts = list(self.ex_folder.get_contacts().values())
        self.assertEqual(len(contacts), 1)
        cid = contacts[0].get_itemid()

        time.sleep(8.0)

        bbdb, bbf = reopen_bb(BB_FILE)
        cons = bbf.find_contacts_by_name(name='ConflictMe')
        self.assertEqual(len(cons), 1)
        cons[0].set_company('BBDBCorp')
        bbf.save()

        update_ex_contact_company(self.exdb, cid, 'EXCorp')

        config.set_conflict_resolve(PROFILE_NAME, '2')

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)

        bbdb, bbf = reopen_bb(BB_FILE)
        cons = bbf.find_contacts_by_name(name='ConflictMe')
        self.assertEqual(len(cons), 1)
        self.assertEqual(cons[0].get_company(), 'BBDBCorp')

        time.sleep(1.5)
        self.ex_folder._refresh_items()
        contacts = list(self.ex_folder.get_contacts().values())
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0].get_company(), 'BBDBCorp')

    ## -----------------------------------------------------------------
    ## Test 14: Bidirectional Additions
    ## -----------------------------------------------------------------

    def test_n_bidirectional_new (self):
        """Add new contacts on both sides independently, sync, verify both exist on both sides."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'BBNew', 'Contact')
        bbf.save()

        create_ex_contact(self.exdb, self.test_gid, 'EXNew', 'Contact')
        time.sleep(2)

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)

        bbdb, bbf = reopen_bb(BB_FILE)
        self.assertEqual(len(bbf.get_contacts()), 2)
        bb_names = sorted([c.get_firstname() for c in bbf.get_contacts().values()])
        self.assertEqual(bb_names, ['BBNew', 'EXNew'])

        self.assertEqual(count_ex_contacts(self.ex_folder), 2)
        self.ex_folder._refresh_items()
        ex_names = sorted([c.get_firstname() for c in self.ex_folder.get_contacts().values()])
        self.assertEqual(ex_names, ['BBNew', 'EXNew'])

    ## -----------------------------------------------------------------
    ## Test 15: Unicode Support
    ## -----------------------------------------------------------------

    def test_o_unicode (self):
        """Create BB contacts with Unicode names, sync, verify EX fields."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'Héctor', 'Muñoz')
        make_bb_contact(bbf, '太郎', '山田')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)

        self.assertEqual(count_ex_contacts(self.ex_folder), 2)
        self.ex_folder._refresh_items()
        ex_names = sorted([c.get_firstname() for c in self.ex_folder.get_contacts().values()])
        self.assertEqual(ex_names, ['Héctor', '太郎'])

    ## -----------------------------------------------------------------
    ## Test 16: Minimal/Empty Fields
    ## -----------------------------------------------------------------

    def test_p_empty_fields (self):
        """Sync a contact with only first name from BB to EX."""
        bbdb, bbf = open_bb(BB_FILE)
        con = BBContact(bbf)
        con.set_firstname('Minimalist')
        bbf.add_contact(con)
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)

        self.assertEqual(count_ex_contacts(self.ex_folder), 1)
        self.ex_folder._refresh_items()
        contacts = list(self.ex_folder.get_contacts().values())
        self.assertEqual(contacts[0].get_firstname(), 'Minimalist')

    ## -----------------------------------------------------------------
    ## Test 17: Field Preservation / Custom Overflow Round-Trip
    ## -----------------------------------------------------------------

    def test_q_field_preservation_roundtrip (self):
        """Test round-trip preservation of non-native/unsupported fields."""
        global config
        bbdb, bbf = open_bb(BB_FILE)
        con = BBContact(bbf)
        con.set_firstname('PreserveFirst')
        con.set_lastname('PreserveLast')
        con.set_middlename('PreserveMiddle')
        con.set_prefix('Mr')
        con.set_suffix('III')
        con.set_nickname('PresNick')
        con.set_company('PresComp1')
        con.add_custom('company', '["PresComp2"]')
        con.add_custom('aka', '["PresNick2", "PresNick3"]')
        con.add_phone_home(('MyCustomHome', '+1-555-0001'))
        con.add_phone_work(('SpecialWork', '+1-555-0002'))
        con.add_custom('my_random_note', 'some_random_value')
        con.add_email_work('work@preserve.com')
        con.add_email_home('home@preserve.com')
        con.add_email_other('other@preserve.com')
        con.set_email_prim('work@preserve.com')
        con.set_gender('Male')
        con.set_birthday('1985-10-25')
        con.set_anniv('2015-05-20')
        con.add_web_home('https://preserve-home.com')
        con.add_web_work('https://preserve-work.com')
        con.add_notes('Important preservation note.')
        bbf.add_contact(con)
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.exdb, bbdb)
        self.assertTrue(result)

        # Force sync EX -> BB on a completely empty BBDB to verify round-trip restoration
        create_empty_bbdb(BB_FILE)
        shutil.copyfile(STATE_SRC, os.path.join(EX_CREDS_DIR, 'state.json'))

        config = Config(asynk_base_dir=ASYNK_BASE_DIR, user_dir=EX_CREDS_DIR)

        bbdb, bbf = open_bb(BB_FILE)
        exdb_new = EXPIMDB(config, client_id=resolved_client_id,
                           tenant_id=resolved_tenant_id,
                           token_cache_path=token_cache)
        create_profile(config, PROFILE_NAME, self.test_gid)

        result = run_sync(config, PROFILE_NAME, exdb_new, bbdb)
        self.assertTrue(result)

        bbdb, bbf = reopen_bb(BB_FILE)
        contacts = list(bbf.get_contacts().values())
        self.assertEqual(len(contacts), 1)
        res_con = contacts[0]

        # Assert all fields match exactly
        self.assertEqual(res_con.get_firstname(), 'PreserveFirst')
        self.assertEqual(res_con.get_lastname(), 'PreserveLast')
        self.assertEqual(res_con.get_middlename(), 'PreserveMiddle')
        self.assertEqual(res_con.get_prefix(), 'Mr')
        self.assertEqual(res_con.get_suffix(), 'III')
        self.assertEqual(res_con.get_nickname(), 'PresNick')
        self.assertEqual(res_con.get_company(), 'PresComp1')
        self.assertEqual(demjson.decode(res_con.get_custom('company')), ["PresComp2"])
        self.assertEqual(demjson.decode(res_con.get_custom('aka')), ["PresNick2", "PresNick3"])
        self.assertEqual(res_con.get_phone_home()[0][0], 'MyCustomHome')
        self.assertEqual(res_con.get_phone_work()[0][0], 'SpecialWork')
        self.assertEqual(res_con.get_custom('my_random_note'), 'some_random_value')
        self.assertEqual(res_con.get_gender(), 'Male')
        self.assertEqual(res_con.get_birthday(), '1985-10-25')
        self.assertEqual(res_con.get_anniv(), '2015-05-20')
        self.assertIn('https://preserve-home.com', res_con.get_web_home())
        self.assertIn('https://preserve-work.com', res_con.get_web_work())
        self.assertIn('Important preservation note.', res_con.get_notes())

## ---------------------------------------------------------------------------
## Main
## ---------------------------------------------------------------------------

def main ():
    global config, resolved_client_id, resolved_tenant_id, token_cache

    client_id = None
    tenant_id = 'common'
    best_effort = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], '',
                                   ['client-id=', 'tenant-id=', 'best-effort'])
    except getopt.error as msg:
        print('Usage: python test_sync_ex_bb.py [--client-id YOUR-CLIENT-ID] '
              '[--tenant-id TENANT] [--best-effort]')
        sys.exit(2)

    for option, arg in opts:
        if option == '--client-id':
            client_id = arg
        elif option == '--tenant-id':
            tenant_id = arg
        elif option == '--best-effort':
            best_effort = True

    setup_user_dir()

    if not os.path.exists(EX_CREDS_DIR):
        os.makedirs(EX_CREDS_DIR)

    ## 1. CLI option
    ## 2. Cached client_id file
    ## 3. config_v10.json
    cached_client_id = None
    cid_file = os.path.join(EX_CREDS_DIR, 'client_id')
    if os.path.exists(cid_file):
        try:
            with open(cid_file, 'r') as f:
                cached_client_id = f.read().strip()
        except Exception:
            pass

    default_client_id = None
    default_tenant_id = 'common'
    confn_dest = os.path.join(USER_DIR, 'config.json')
    if os.path.exists(confn_dest):
        try:
            with open(confn_dest, 'r') as f:
                cfg = demjson.decode(f.read())
                if cfg and 'ex' in cfg['db_config']:
                    cfg = cfg['db_config']
                    default_client_id = cfg['ex'].get('client_id')
                    default_tenant_id = cfg['ex'].get('tenant_id', 'common')
        except Exception:
            pass

    resolved_client_id = client_id or cached_client_id or default_client_id
    resolved_tenant_id = tenant_id if tenant_id != 'common' else default_tenant_id

    if not resolved_client_id:
        if best_effort:
            logging.warning('No client_id provided or cached. Skipping EX sync tests.')
            sys.exit(0)
        else:
            print('ERROR: Exchange client ID is required.')
            print('Usage: make sync-ex-bb EX_CLIENT_ID=YOUR-CLIENT-ID')
            sys.exit(1)

    # Save client_id to cache for next time
    if client_id:
        try:
            with open(cid_file, 'w') as f:
                f.write(client_id)
        except Exception:
            pass

    token_cache = os.path.join(EX_CREDS_DIR, 'msal_token_cache.bin')
    config = Config(asynk_base_dir=ASYNK_BASE_DIR, user_dir=EX_CREDS_DIR)

    sys.argv = [sys.argv[0]] + args
    unittest.main(verbosity=2)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()
