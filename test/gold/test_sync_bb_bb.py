# -*- coding: utf-8 -*-
##
## Created : Fri May 16 01:18:00 IST 2026
## SPDX-FileCopyrightText: 2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
#####
##
## Gold tests for the ASynK sync engine using two BBDB stores.
## Fully offline — no network or credentials required.
##
## Usage: python test_sync_bb_bb.py [--debug]
##

import logging, os, shutil, sys, time, unittest

## Fix sys.path so we can import asynk modules
CUR_DIR     = os.path.abspath(os.path.dirname(__file__))
DIR_PATH    = os.path.abspath(os.path.join(CUR_DIR, '..', '..'))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk')]
sys.path    = EXTRA_PATHS + sys.path

from state      import Config
from pimdb_bb   import BBPIMDB
from folder_bb  import BBContactsFolder
from contact_bb import BBContact
from sync       import Sync
import utils

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------

ASYNK_BASE_DIR = DIR_PATH
USER_DIR       = os.path.abspath(os.path.join(CUR_DIR, 'user_dir'))
STATE_SRC      = os.path.join(DIR_PATH, 'state.init.json')
CONF_SRC       = os.path.join(DIR_PATH, 'config', 'config_v6.json')

PROFILE_NAME   = 'testbbbb'
BB1_FILE       = os.path.abspath(os.path.join(CUR_DIR, 'test_sync_bb1.bbdb'))
BB2_FILE       = os.path.abspath(os.path.join(CUR_DIR, 'test_sync_bb2.bbdb'))

## Module-level config — set up once by main()
config = None

## ---------------------------------------------------------------------------
## Helpers
## ---------------------------------------------------------------------------

def setup_user_dir ():
    """Create (or re-create) a clean user_dir with state + config files."""
    if os.path.exists(USER_DIR):
        shutil.rmtree(USER_DIR)
    os.makedirs(USER_DIR)
    shutil.copyfile(STATE_SRC, os.path.join(USER_DIR, 'state.json'))
    shutil.copyfile(CONF_SRC, os.path.join(USER_DIR, 'config.json'))

def create_empty_bbdb (fn):
    """Create a minimal valid BBDB file."""
    with open(fn, 'w', encoding='utf-8') as f:
        f.write(';; -*-coding: utf-8-emacs;-*-\n')
        f.write(';;; file-format: 7\n')

def open_bb (fn):
    """Open a BBDB store and return (BBPIMDB, default_folder)."""
    db = BBPIMDB(config, fn)
    ms = db.get_def_msgstore()
    f  = ms.get_folder(ms.get_def_folder_name())
    return db, f

def reopen_bb (fn):
    """Re-parse a BBDB file to get fresh state from disk."""
    return open_bb(fn)

def create_profile (conf, pname, fid1='default', fid2='default'):
    """Programmatically create a sync profile for bb<->bb."""
    profile = conf.get_profile_defaults()
    profile.update({
        'coll_1': {'dbid': 'bb', 'stid': BB1_FILE, 'foid': fid1},
        'coll_2': {'dbid': 'bb', 'stid': BB2_FILE, 'foid': fid2},
        'olgid': None,
        'sync_dir': 'SYNC2WAY',
        'sync_state': None,
        'conflict_resolve': '1',
    })
    conf.add_profile(pname, profile)

def run_sync (conf, pname, db1, db2, dirn=None):
    """Run a sync between two PIMDBs using the given profile."""
    dbs = {0: db1, 1: db2}

    # Fake the pimdbs list as expected by Sync.__init__
    # Sync expects pimdbs[0] and pimdbs[1] accessible by numeric index
    startt = conf.get_curr_time()
    sync = Sync(conf, pname, [db1, db2])
    if not dirn:
        dirn = conf.get_sync_dir(pname)
    result = sync.sync(dirn)
    if result:
        conf.set_last_sync_start(pname, val=startt)
        conf.set_last_sync_stop(pname)
        sync.save_item_lists()
    return result

def make_contact (folder, first, last, **kwargs):
    """Create a BBContact with specified fields and add to folder."""
    con = BBContact(folder)
    con.set_firstname(first)
    con.set_lastname(last)
    for key, val in kwargs.items():
        setter = getattr(con, 'set_' + key, None)
        if setter:
            setter(val)
        else:
            adder = getattr(con, 'add_' + key, None)
            if adder:
                adder(val)
    folder.add_contact(con)
    return con

## ---------------------------------------------------------------------------
## Test Cases
## ---------------------------------------------------------------------------

class TestSyncBBBBBase(unittest.TestCase):
    """Base class with common setUp/tearDown for BB<->BB sync tests."""

    def setUp (self):
        """Create fresh BBDB files and a sync profile for each test."""
        import gc as _gc

        # Force garbage collection first so that any lingering
        # BBContactsFolder.__del__ finalizers flush BEFORE we
        # create fresh empty BBDB files.
        _gc.collect()

        # Reset config from disk to clear any stale profile state
        setup_user_dir()

        # NOW create fresh empty BBDB files (after finalizers have run)
        create_empty_bbdb(BB1_FILE)
        create_empty_bbdb(BB2_FILE)

        self.__class__.config = Config(asynk_base_dir=ASYNK_BASE_DIR,
                                       user_dir=USER_DIR)
        global config
        config = self.__class__.config

        # Create a fresh profile
        if not config.profile_exists(PROFILE_NAME):
            create_profile(config, PROFILE_NAME)

    def tearDown (self):
        """Remove temporary BBDB files."""
        for fn in [BB1_FILE, BB2_FILE]:
            if os.path.exists(fn):
                os.remove(fn)

    def _open_stores (self):
        """Open both BBDB stores. Returns (db1, f1, db2, f2)."""
        db1, f1 = open_bb(BB1_FILE)
        db2, f2 = open_bb(BB2_FILE)
        return db1, f1, db2, f2


class TestInitialSync(TestSyncBBBBBase):
    """Section 1: Initial sync (first run) tests."""

    def test_1_1_empty_to_empty (self):
        """Sync two empty folders — should succeed with zero items."""
        db1, f1, db2, f2 = self._open_stores()
        result = run_sync(config, PROFILE_NAME, db1, db2)
        self.assertTrue(result)

        # Both should still be empty
        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = reopen_bb(BB2_FILE)
        self.assertEqual(len(f1.get_contacts()), 0)
        self.assertEqual(len(f2.get_contacts()), 0)

    def test_1_2_populated_to_empty (self):
        """Create contacts in bb1, sync to empty bb2."""
        db1, f1 = open_bb(BB1_FILE)
        make_contact(f1, 'Alice', 'Smith')
        make_contact(f1, 'Bob', 'Jones')
        make_contact(f1, 'Carol', 'White')
        f1.save()

        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = open_bb(BB2_FILE)
        result = run_sync(config, PROFILE_NAME, db1, db2)
        self.assertTrue(result)

        # Verify bb2 now has 3 contacts
        db2, f2 = reopen_bb(BB2_FILE)
        self.assertEqual(len(f2.get_contacts()), 3)

        # Verify names
        names = sorted([c.get_firstname() for c in f2.get_contacts().values()])
        self.assertEqual(names, ['Alice', 'Bob', 'Carol'])

    def test_1_3_field_fidelity (self):
        """Create a contact with many fields, sync, verify all survive."""
        db1, f1 = open_bb(BB1_FILE)
        con = BBContact(f1)
        con.set_firstname('Fidelity')
        con.set_lastname('Test')
        con.set_prefix('Dr')
        con.set_suffix('Jr')
        con.set_nickname('Fiddy')
        con.set_company('TestCorp')
        con.set_title('Engineer')
        con.set_dept('R&D')
        con.add_email_home('fiddy@home.com')
        con.add_email_work('fiddy@work.com')
        con.set_email_prim('fiddy@work.com')
        con.add_phone_home(('Home', '+1-555-0001'))
        con.add_phone_work(('Work', '+1-555-0002'))
        con.add_phone_mob(('Mobile', '+1-555-0003'))
        con.add_notes('A very important note.')
        f1.add_contact(con)
        f1.save()

        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = open_bb(BB2_FILE)
        result = run_sync(config, PROFILE_NAME, db1, db2)
        self.assertTrue(result)

        db2, f2 = reopen_bb(BB2_FILE)
        cons = f2.find_contacts_by_name(name='Fidelity')
        self.assertEqual(len(cons), 1)
        c = cons[0]

        self.assertEqual(c.get_firstname(), 'Fidelity')
        self.assertEqual(c.get_lastname(), 'Test')
        self.assertEqual(c.get_prefix(), 'Dr')
        self.assertEqual(c.get_suffix(), 'Jr')
        self.assertEqual(c.get_nickname(), 'Fiddy')
        self.assertEqual(c.get_company(), 'TestCorp')
        self.assertEqual(c.get_title(), 'Engineer')
        self.assertEqual(c.get_dept(), 'R&D')

        # Emails may be re-classified by domain; just verify they exist
        all_emails = (c.get_email_home() + c.get_email_work() +
                      c.get_email_other())
        self.assertIn('fiddy@home.com', all_emails)
        self.assertIn('fiddy@work.com', all_emails)

        notes = c.get_notes()
        self.assertTrue(len(notes) > 0)
        self.assertIn('A very important note.', notes[0])


class TestIncrementalSync(TestSyncBBBBBase):
    """Section 2: Incremental sync (second run) tests."""

    def _do_initial_sync (self):
        """Helper: populate bb1 with 3 contacts, sync to bb2, return."""
        db1, f1 = open_bb(BB1_FILE)
        make_contact(f1, 'Dave', 'Alpha')
        make_contact(f1, 'Eve', 'Beta')
        make_contact(f1, 'Frank', 'Gamma')
        f1.save()

        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = open_bb(BB2_FILE)
        result = run_sync(config, PROFILE_NAME, db1, db2)
        self.assertTrue(result)

    def test_2_1_no_changes (self):
        """Sync twice with no modifications — second should be a no-op."""
        self._do_initial_sync()

        # Second sync
        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = reopen_bb(BB2_FILE)
        result = run_sync(config, PROFILE_NAME, db1, db2)
        self.assertTrue(result)

        # Counts should be unchanged
        db2, f2 = reopen_bb(BB2_FILE)
        self.assertEqual(len(f2.get_contacts()), 3)

    def test_2_2_add_new_contact (self):
        """After initial sync, add 1 new contact to bb1, re-sync."""
        self._do_initial_sync()

        # Add a new contact to bb1
        db1, f1 = reopen_bb(BB1_FILE)
        make_contact(f1, 'Grace', 'Delta')
        f1.save()

        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = reopen_bb(BB2_FILE)
        result = run_sync(config, PROFILE_NAME, db1, db2)
        self.assertTrue(result)

        db2, f2 = reopen_bb(BB2_FILE)
        self.assertEqual(len(f2.get_contacts()), 4)
        names = sorted([c.get_firstname() for c in f2.get_contacts().values()])
        self.assertIn('Grace', names)

    def test_2_3_update_existing_contact (self):
        """After initial sync, modify a field on a src contact. Re-sync."""
        self._do_initial_sync()

        # Modify a contact in bb1
        db1, f1 = reopen_bb(BB1_FILE)
        cons = f1.find_contacts_by_name(name='Dave')
        self.assertEqual(len(cons), 1)
        time.sleep(1.1)  # Ensure BBDB timestamp (>1s resolution) beats last_sync_stop
        cons[0].set_company('NewCorp')
        f1.save()

        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = reopen_bb(BB2_FILE)
        result = run_sync(config, PROFILE_NAME, db1, db2)
        self.assertTrue(result)

        db2, f2 = reopen_bb(BB2_FILE)
        cons = f2.find_contacts_by_name(name='Dave')
        self.assertEqual(len(cons), 1)
        self.assertEqual(cons[0].get_company(), 'NewCorp')

    def test_2_7_delete_contact (self):
        """After initial sync, delete a contact from src. Re-sync."""
        self._do_initial_sync()

        db1, f1 = reopen_bb(BB1_FILE)
        cons = f1.find_contacts_by_name(name='Dave')
        self.assertEqual(len(cons), 1)
        f1.del_itemids([cons[0].get_itemid()])
        f1.save()

        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = reopen_bb(BB2_FILE)
        result = run_sync(config, PROFILE_NAME, db1, db2)
        self.assertTrue(result)

        db2, f2 = reopen_bb(BB2_FILE)
        cons = f2.find_contacts_by_name(name='Dave')
        self.assertEqual(len(cons), 0)
        self.assertEqual(len(f2.get_contacts()), 2)

    def test_2_4_empty_fields (self):
        """Sync a minimal contact (name only) — should not crash."""
        db1, f1 = open_bb(BB1_FILE)
        con = BBContact(f1)
        con.set_firstname('Minimal')
        f1.add_contact(con)
        f1.save()

        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = open_bb(BB2_FILE)
        result = run_sync(config, PROFILE_NAME, db1, db2)
        self.assertTrue(result)

        db2, f2 = reopen_bb(BB2_FILE)
        self.assertEqual(len(f2.get_contacts()), 1)

    def test_2_5_unicode (self):
        """Sync contacts with non-ASCII characters."""
        db1, f1 = open_bb(BB1_FILE)
        make_contact(f1, 'Héctor', 'Muñoz')
        make_contact(f1, '太郎', '山田')
        f1.save()

        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = open_bb(BB2_FILE)
        result = run_sync(config, PROFILE_NAME, db1, db2)
        self.assertTrue(result)

        db2, f2 = reopen_bb(BB2_FILE)
        self.assertEqual(len(f2.get_contacts()), 2)
        names = [c.get_firstname() for c in f2.get_contacts().values()]
        self.assertIn('Héctor', names)
        self.assertIn('太郎', names)

    def test_2_6_idempotent_triple_sync (self):
        """Sync the same data 3 times — third should still be a no-op."""
        self._do_initial_sync()

        for _ in range(2):
            db1, f1 = reopen_bb(BB1_FILE)
            db2, f2 = reopen_bb(BB2_FILE)
            result = run_sync(config, PROFILE_NAME, db1, db2)
            self.assertTrue(result)

        db2, f2 = reopen_bb(BB2_FILE)
        self.assertEqual(len(f2.get_contacts()), 3)


class TestSyncTagPersistence(TestSyncBBBBBase):
    """Section 4.5: Verify sync tags are written and readable."""

    def test_4_5_sync_tags_written (self):
        """After sync, contacts should have sync tags linking them across
        the two stores."""
        db1, f1 = open_bb(BB1_FILE)
        make_contact(f1, 'TagTest', 'One')
        f1.save()

        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = open_bb(BB2_FILE)
        result = run_sync(config, PROFILE_NAME, db1, db2)
        self.assertTrue(result)

        # Re-read both stores
        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = reopen_bb(BB2_FILE)

        # bb1 contact should have a sync tag pointing to bb2
        stag1 = config.make_sync_label(PROFILE_NAME, 'bb')
        for iid, con in f1.get_contacts().items():
            tags = con.get_sync_tags()
            self.assertTrue(len(tags) > 0,
                            'bb1 contact should have sync tags after sync')

        # bb2 contact should have a sync tag pointing to bb1
        for iid, con in f2.get_contacts().items():
            tags = con.get_sync_tags()
            self.assertTrue(len(tags) > 0,
                            'bb2 contact should have sync tags after sync')


class TestLargeBatch(TestSyncBBBBBase):
    """Section 4.3/4.6: Large batch sync."""

    def test_4_3_large_batch (self):
        """Sync 50+ contacts at once."""
        db1, f1 = open_bb(BB1_FILE)
        for i in range(60):
            make_contact(f1, 'Batch%03d' % i, 'Contact')
        f1.save()

        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = open_bb(BB2_FILE)
        result = run_sync(config, PROFILE_NAME, db1, db2)
        self.assertTrue(result)

        db2, f2 = reopen_bb(BB2_FILE)
        self.assertEqual(len(f2.get_contacts()), 60)


class TestConflictResolution(TestSyncBBBBBase):
    """Section 3: Two-Way Conflict Resolution."""

    def _do_initial_sync(self):
        db1, f1 = open_bb(BB1_FILE)
        make_contact(f1, 'Conflict', 'Tester', company='OldCorp')
        f1.save()

        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = open_bb(BB2_FILE)
        result = run_sync(config, PROFILE_NAME, db1, db2)
        self.assertTrue(result)

    def test_3_1_bidirectional_new(self):
        """Add a new contact to each side independently. Sync."""
        db1, f1 = open_bb(BB1_FILE)
        make_contact(f1, 'Left', 'Side')
        f1.save()

        db2, f2 = open_bb(BB2_FILE)
        make_contact(f2, 'Right', 'Side')
        f2.save()

        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = reopen_bb(BB2_FILE)
        result = run_sync(config, PROFILE_NAME, db1, db2)
        self.assertTrue(result)

        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = reopen_bb(BB2_FILE)
        self.assertEqual(len(f1.get_contacts()), 2)
        self.assertEqual(len(f2.get_contacts()), 2)
        names = sorted([c.get_firstname() for c in f1.get_contacts().values()])
        self.assertEqual(names, ['Left', 'Right'])

    def test_3_3_conflict_db1_wins(self):
        """Modify the same contact on both sides. db1 wins."""
        self._do_initial_sync()

        time.sleep(1.1)  # Ensure timestamp beats last sync
        # Modify bb1
        db1, f1 = reopen_bb(BB1_FILE)
        c1 = f1.find_contacts_by_name(name='Conflict')[0]
        c1.set_company('Corp1')
        f1.save()

        # Modify bb2
        db2, f2 = reopen_bb(BB2_FILE)
        c2 = f2.find_contacts_by_name(name='Conflict')[0]
        c2.set_company('Corp2')
        f2.save()

        # Set db1 to win ('1')
        config.set_conflict_resolve(PROFILE_NAME, '1')

        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = reopen_bb(BB2_FILE)
        result = run_sync(config, PROFILE_NAME, db1, db2)
        self.assertTrue(result)

        db2, f2 = reopen_bb(BB2_FILE)
        c2 = f2.find_contacts_by_name(name='Conflict')[0]
        self.assertEqual(c2.get_company(), 'Corp1')

    def test_3_4_conflict_db2_wins(self):
        """Modify the same contact on both sides. db2 wins."""
        self._do_initial_sync()

        time.sleep(1.1)  # Ensure timestamp beats last sync
        # Modify bb1
        db1, f1 = reopen_bb(BB1_FILE)
        c1 = f1.find_contacts_by_name(name='Conflict')[0]
        c1.set_company('Corp1')
        f1.save()

        # Modify bb2
        db2, f2 = reopen_bb(BB2_FILE)
        c2 = f2.find_contacts_by_name(name='Conflict')[0]
        c2.set_company('Corp2')
        f2.save()

        # Set db2 to win
        config.set_conflict_resolve(PROFILE_NAME, '2')

        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = reopen_bb(BB2_FILE)
        result = run_sync(config, PROFILE_NAME, db1, db2)
        self.assertTrue(result)

        db1, f1 = reopen_bb(BB1_FILE)
        c1 = f1.find_contacts_by_name(name='Conflict')[0]
        self.assertEqual(c1.get_company(), 'Corp2')


class TestOneWaySync(TestSyncBBBBBase):
    """Section 5: One-Way Sync."""

    def setUp(self):
        super().setUp()
        # Change the sync direction to 1-way
        config.set_sync_dir(PROFILE_NAME, 'SYNC1WAY')

    def test_5_1_sync1way_basic(self):
        """Create contacts in src, sync 1-way. Verify they appear in dst."""
        db1, f1 = open_bb(BB1_FILE)
        make_contact(f1, 'OneWay', 'Test')
        f1.save()

        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = open_bb(BB2_FILE)
        result = run_sync(config, PROFILE_NAME, db1, db2)
        self.assertTrue(result)

        db2, f2 = reopen_bb(BB2_FILE)
        self.assertEqual(len(f2.get_contacts()), 1)

    def test_5_2_sync1way_ignores_dst_changes(self):
        """After 1-way sync, modify dst. Re-sync. Verify src is unchanged."""
        db1, f1 = open_bb(BB1_FILE)
        make_contact(f1, 'OneWay', 'Test')
        f1.save()

        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = open_bb(BB2_FILE)
        result = run_sync(config, PROFILE_NAME, db1, db2)
        self.assertTrue(result)

        # Add a new contact to dst (db2)
        db2, f2 = reopen_bb(BB2_FILE)
        make_contact(f2, 'DstOnly', 'Contact')
        f2.save()

        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = reopen_bb(BB2_FILE)
        result = run_sync(config, PROFILE_NAME, db1, db2)
        self.assertTrue(result)

        # Verify src is still 1 contact
        db1, f1 = reopen_bb(BB1_FILE)
        db2, f2 = reopen_bb(BB2_FILE)
        self.assertEqual(len(f1.get_contacts()), 1)
        self.assertEqual(len(f2.get_contacts()), 2)


## ---------------------------------------------------------------------------
## Main
## ---------------------------------------------------------------------------

def main ():
    global config

    setup_user_dir()
    config = Config(asynk_base_dir=ASYNK_BASE_DIR, user_dir=USER_DIR)

    sys.argv = [sys.argv[0]]
    unittest.main(verbosity=2)

if __name__ == '__main__':
    if '--debug' in sys.argv:
        logging.getLogger().setLevel(logging.DEBUG)
        sys.argv.remove('--debug')
    else:
        logging.getLogger().setLevel(logging.ERROR)

    main()
