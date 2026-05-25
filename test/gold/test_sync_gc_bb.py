# -*- coding: utf-8 -*-
##
## Created : Fri May 16 01:27:00 IST 2026
## SPDX-FileCopyrightText: 2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
#####
##
## Gold tests for the ASynK sync engine using Google Contacts <-> BBDB.
## Requires live Google credentials — runs best-effort when invoked via
## 'make all', hard error when invoked via 'make sync-gc'.
##
## Usage: python test_sync_gc_bb.py [--cs /path/to/creds.json]
##                                  [--user label]
##                                  [--best-effort]
##

import getopt, glob, logging, os, shutil, sys, time, unittest

## Fix sys.path so we can import asynk modules
CUR_DIR     = os.path.abspath(os.path.dirname(__file__))
DIR_PATH    = os.path.abspath(os.path.join(CUR_DIR, '..', '..'))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk')]
sys.path    = EXTRA_PATHS + sys.path

from state       import Config
from pimdb_gc    import GCPIMDB
from pimdb_bb    import BBPIMDB
from contact_bb  import BBContact
from sync        import Sync

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------

ASYNK_BASE_DIR = DIR_PATH
USER_DIR       = os.path.abspath(os.path.join(CUR_DIR, 'user_dir'))
STATE_SRC      = os.path.join(DIR_PATH, 'state.init.json')
CONF_SRC       = os.path.join(DIR_PATH, 'config', 'config_v6.json')

GC_CREDS_DIR   = os.path.abspath(os.path.join(CUR_DIR, 'gc_creds'))
BB_FILE        = os.path.abspath(os.path.join(CUR_DIR, 'test_sync_gc_bb.bbdb'))

PROFILE_NAME   = 'testgcbb'
TEST_GROUP     = 'ASynK Sync Test (safe to delete)'

## Module-level state
config  = None
cs_file = None
gc_user = 'test'

## ---------------------------------------------------------------------------
## Multi-account support — distribute test classes across available accounts
## to spread API quota load.  See gc_add_account.py to add accounts.
## ---------------------------------------------------------------------------

_gc_accounts = []   # populated by main(); list of user labels
_gc_acct_idx = 0    # next account to assign (per-test rotation)

def discover_gc_accounts (creds_dir):
    """Return sorted list of user labels from *.token.pickle files."""
    tokens = sorted(glob.glob(os.path.join(creds_dir, '*.token.pickle')))
    return [os.path.basename(t).replace('.token.pickle', '') for t in tokens]

def _get_account_labels ():
    """Return the list of account labels to use.  Falls back to [gc_user]
    if no accounts have been discovered."""
    return _gc_accounts if _gc_accounts else [gc_user]

## ---------------------------------------------------------------------------
## Helpers
## ---------------------------------------------------------------------------

def print_suite_banner(suite_name):
    print('\n' + '='*80)
    print('>>> INITIALIZING TEST SUITE: %s' % suite_name)
    print('='*80)

def print_test_banner(test_name, account, pool_idx):
    print('\n' + '-'*80)
    print('>> RUNNING TEST: %s' % test_name)
    print('>> USING ACCOUNT: %s (Pool index: %d)' % (account, pool_idx))
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

def create_profile (conf, pname, gc_fid):
    """Create a sync profile for gc<->bb."""
    profile = conf.get_profile_defaults()
    profile.update({
        'coll_1': {'dbid': 'gc', 'stid': None, 'foid': gc_fid},
        'coll_2': {'dbid': 'bb', 'stid': BB_FILE, 'foid': 'default'},
        'olgid': None,
        'sync_dir': 'SYNC2WAY',
        'sync_state': None,
        'conflict_resolve': '1',
    })
    conf.add_profile(pname, profile)

def run_sync (conf, pname, gcdb, bbdb, dirn=None):
    """Run a sync between GC and BB PIMDBs."""
    startt = conf.get_curr_time()
    sync = Sync(conf, pname, [gcdb, bbdb])
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

def create_gc_contact (gcdb, gid, first, last, email=None, phone=None):
    """Create a contact directly in Google and return the resource name."""
    svc = gcdb.get_service()
    body = {
        'names': [{'givenName': first, 'familyName': last}],
        'memberships': [{
            'contactGroupMembership': {
                'contactGroupResourceName': gid
            }
        }],
    }
    if email:
        body['emailAddresses'] = [{'value': email, 'type': 'work'}]
    if phone:
        body['phoneNumbers'] = [{'value': phone, 'type': 'mobile'}]

    person = svc.people().createContact(body=body).execute()
    return person.get('resourceName')

def delete_gc_contact (gcdb, resource_name):
    """Delete a contact from Google by resource name."""
    svc = gcdb.get_service()
    svc.people().deleteContact(resourceName=resource_name).execute()

def update_gc_contact_company (gcdb, resource_name, company):
    """Update the company/organization of a Google contact."""
    svc = gcdb.get_service()
    current = svc.people().get(
        resourceName=resource_name,
        personFields='names,organizations,metadata'
    ).execute()
    current['organizations'] = [{
        'name': company,
        'type': 'work'
    }]
    svc.people().updateContact(
        resourceName=resource_name,
        body=current,
        updatePersonFields='organizations',
        personFields='organizations'
    ).execute()


def count_gc_contacts (gc_folder):
    """Return the number of contacts in the GC folder."""
    persons = gc_folder._get_group_contacts()
    return len(persons) if persons else 0

def cleanup_gc_contacts (gc_folder, gcdb):
    """Delete all contacts in the GC test folder."""
    persons = gc_folder._get_group_contacts()
    if not persons:
        return
    svc = gcdb.get_service()
    rnames = [p.get('resourceName') for p in persons if p.get('resourceName')]

    BATCH_SIZE = 200
    for i in range(0, len(rnames), BATCH_SIZE):
        batch = rnames[i:i + BATCH_SIZE]
        try:
            svc.people().batchDeleteContacts(body={'resourceNames': batch}).execute()
        except Exception as e:
            logging.warning('cleanup: batch delete failed: %s', e)

## ---------------------------------------------------------------------------
## Test Cases
## ---------------------------------------------------------------------------

class TestSyncGCBB(unittest.TestCase):
    """GC <-> BB sync engine integration tests.

    Uses a pool of Google accounts (one GCPIMDB + dedicated test group per
    account) created in setUpClass.  setUp rotates through the pool so
    consecutive tests hit different accounts, spreading API quota load.
    The BB side uses a temp .bbdb file reset per test.
    """

    @classmethod
    def setUpClass (cls):
        print_suite_banner(cls.__name__)
        if cs_file is None:
            raise unittest.SkipTest(
                'No credentials available; skipping GC sync tests.')

        ## Build a pool of (label, gcdb, gc_folder, test_gid) tuples —
        ## one per available account.
        cls._account_pool = []
        labels = _get_account_labels()
        for label in labels:
            try:
                gcdb = GCPIMDB(config, label, cs_file)
            except Exception as e:
                logging.warning('Skipping account %s: %s', label, e)
                continue

            ## Each account gets its own test group (with label suffix
            ## to avoid name collisions between accounts).
            group_name = TEST_GROUP if len(labels) == 1 \
                         else '%s (%s)' % (TEST_GROUP, label)
            try:
                test_gid = gcdb.new_folder(group_name)
            except Exception:
                ## Group may already exist from a previous incomplete run
                test_gid = None
                for f in gcdb.get_contacts_folders():
                    if f.get_name() == group_name:
                        test_gid = f.get_itemid()
                        break
                if test_gid is None:
                    logging.warning('Could not create test group for %s', label)
                    continue

            gc_folder = None
            for f in gcdb.get_contacts_folders():
                if f.get_itemid() == test_gid:
                    gc_folder = f
                    break

            if gc_folder is None:
                logging.warning('Could not find test group for %s', label)
                continue

            cls._account_pool.append((label, gcdb, gc_folder, test_gid))
            logging.info('Account pool: added %s (group %s)', label, test_gid)

        if not cls._account_pool:
            raise unittest.SkipTest(
                'No working Google accounts available')

        logging.info('Account pool ready: %d account(s)',
                     len(cls._account_pool))
        cls._pool_idx = 0

        ## Set initial values so setUp can reference them on first run
        label, gcdb, gc_folder, test_gid = cls._account_pool[0]
        cls.gcdb = gcdb
        cls.gc_folder = gc_folder
        cls.test_gid = test_gid

        ## Create the initial sync profile
        create_profile(config, PROFILE_NAME, test_gid)

    @classmethod
    def tearDownClass (cls):
        """Delete the test groups and all their contacts for every account."""
        for label, gcdb, gc_folder, test_gid in getattr(cls, '_account_pool', []):
            try:
                cleanup_gc_contacts(gc_folder, gcdb)
                time.sleep(1)
                gcdb.del_folder(test_gid)
            except Exception as e:
                logging.warning('Cleanup failed for %s: %s', label, e)
        time.sleep(2)

    def setUp (self):
        """Fresh BBDB file for each test.  Rotate to the next Google account
        in the pool, reset its folder, and rebuild the sync profile."""
        import gc as _gc
        _gc.collect()

        ## Rotate to next account
        pool = self.__class__._account_pool
        idx = self.__class__._pool_idx % len(pool)
        self.__class__._pool_idx += 1
        label, gcdb, gc_folder, test_gid = pool[idx]

        self.gcdb = gcdb
        self.gc_folder = gc_folder
        self.test_gid = test_gid
        print_test_banner(self._testMethodName, label, idx)

        create_empty_bbdb(BB_FILE)
        cleanup_gc_contacts(self.gc_folder, self.gcdb)
        self.gc_folder.reset_contacts()
        time.sleep(2)   # let Google propagate deletes

        ## Reset state.json within GC_CREDS_DIR to clear stale item lists
        ## and profile data, but preserve credentials and config.
        shutil.copyfile(STATE_SRC, os.path.join(GC_CREDS_DIR, 'state.json'))

        global config
        config = Config(asynk_base_dir=ASYNK_BASE_DIR, user_dir=GC_CREDS_DIR)

        self.gcdb.set_config(config)
        self.gc_folder.set_config(config)
        create_profile(config, PROFILE_NAME, self.test_gid)

    def tearDown (self):
        if os.path.exists(BB_FILE):
            os.remove(BB_FILE)

    ## -----------------------------------------------------------------
    ## Test 1: BB -> GC initial sync
    ## -----------------------------------------------------------------

    def test_a_bb_to_gc_initial (self):
        """Create contacts in BB, sync to empty GC group."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'SyncAlice', 'BB2GC')
        make_bb_contact(bbf, 'SyncBob', 'BB2GC')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
        self.assertTrue(result)

        # Verify GC has 2 contacts
        cnt = count_gc_contacts(self.gc_folder)
        self.assertEqual(cnt, 2, 'Expected 2 contacts in GC, got %d' % cnt)

    ## -----------------------------------------------------------------
    ## Test 2: GC -> BB initial sync
    ## -----------------------------------------------------------------

    def test_b_gc_to_bb_initial (self):
        """Create contacts in GC, sync to empty BB."""
        create_gc_contact(self.gcdb, self.test_gid,
                          'SyncCarol', 'GC2BB', email='carol@test.com')
        create_gc_contact(self.gcdb, self.test_gid,
                          'SyncDave', 'GC2BB', phone='+1-555-9999')
        time.sleep(2)  # API propagation

        bbdb, bbf = open_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
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
        create_gc_contact(self.gcdb, self.test_gid,
                          'NoOp', 'Test')
        time.sleep(2)

        bbdb, bbf = open_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
        self.assertTrue(result)

        # Second sync — should be no-op
        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
        self.assertTrue(result)

        bbdb, bbf = reopen_bb(BB_FILE)
        self.assertEqual(len(bbf.get_contacts()), 1)

    ## -----------------------------------------------------------------
    ## Test 4: Sync tag persistence
    ## -----------------------------------------------------------------

    def test_d_sync_tags (self):
        """After sync, BB contacts should carry sync tags."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'TagTest', 'GCBB')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
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
        """Create a rich BB contact, sync to GC, verify key fields."""
        bbdb, bbf = open_bb(BB_FILE)
        con = BBContact(bbf)
        con.set_firstname('Fidelity')
        con.set_lastname('GCBBTest')
        con.set_prefix('Dr')
        con.set_nickname('Fiddy')
        con.set_company('TestCorp')
        con.add_email_work('fiddy@work.com')
        con.add_phone_mob(('Mobile', '+1-555-7777'))
        con.add_notes('Important GC-BB note.')
        bbf.add_contact(con)
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
        self.assertTrue(result)

        # Verify the contact exists in GC
        cnt = count_gc_contacts(self.gc_folder)
        self.assertEqual(cnt, 1)

        # Read the GC contact and check fields
        persons = self.gc_folder._get_group_contacts()
        p = persons[0]
        names = p.get('names', [{}])
        self.assertEqual(names[0].get('givenName'), 'Fidelity')
        self.assertEqual(names[0].get('familyName'), 'GCBBTest')

    ## -----------------------------------------------------------------
    ## Test 6: Add new contact incrementally
    ## -----------------------------------------------------------------

    def test_f_incremental_add (self):
        """After initial sync, add a new BB contact and re-sync."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'First', 'Batch')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
        self.assertTrue(result)
        self.assertEqual(count_gc_contacts(self.gc_folder), 1)

        # Add another contact
        bbdb, bbf = reopen_bb(BB_FILE)
        make_bb_contact(bbf, 'Second', 'Batch')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
        self.assertTrue(result)

        self.assertEqual(count_gc_contacts(self.gc_folder), 2)

    ## -----------------------------------------------------------------
    ## Test 7: Batch chunking
    ## -----------------------------------------------------------------

    def test_g_batch_chunking (self):
        """Sync enough contacts to trigger multiple API batches.

        Instead of creating 200+ contacts (slow and quota-heavy), we
        temporarily lower BATCH_SIZE to 1 and sync 3 contacts.  This
        exercises the exact same chunking code paths with minimal quota hit.
        """
        from folder_gc import GCContactsFolder
        orig_batch = GCContactsFolder.BATCH_SIZE
        GCContactsFolder.BATCH_SIZE = 1
        try:
            N = 3
            bbdb, bbf = open_bb(BB_FILE)
            for i in range(N):
                make_bb_contact(bbf, 'Chunk%02d' % i, 'Test')
            bbf.save()

            bbdb, bbf = reopen_bb(BB_FILE)
            result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
            self.assertTrue(result)

            cnt = count_gc_contacts(self.gc_folder)
            self.assertEqual(cnt, N,
                             'Expected %d contacts in GC, got %d' % (N, cnt))
        finally:
            GCContactsFolder.BATCH_SIZE = orig_batch

    ## -----------------------------------------------------------------
    ## Test 8: Incremental update
    ## -----------------------------------------------------------------

    def test_h_incremental_update (self):
        """After initial sync, modify a BB contact field. Re-sync.
        Verify the GC contact is updated."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'UpdateMe', 'TestGCBB', company='OldCorp')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
        self.assertTrue(result)
        self.assertEqual(count_gc_contacts(self.gc_folder), 1)

        # Modify the contact in BB
        time.sleep(1.1)  # BBDB timestamp must beat last_sync_stop
        bbdb, bbf = reopen_bb(BB_FILE)
        cons = bbf.find_contacts_by_name(name='UpdateMe')
        self.assertEqual(len(cons), 1)
        cons[0].set_company('NewCorp')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
        self.assertTrue(result)

        # Verify GC contact has the updated company
        persons = self.gc_folder._get_group_contacts()
        self.assertEqual(len(persons), 1)
        orgs = persons[0].get('organizations', [])
        self.assertTrue(len(orgs) > 0, 'GC contact should have organizations')
        self.assertEqual(orgs[0].get('name'), 'NewCorp')

    ## -----------------------------------------------------------------
    ## Test 9: Delete propagation
    ## -----------------------------------------------------------------

    def test_i_delete_propagation (self):
        """After initial sync of 2 BB contacts, delete 1 from BB.
        Re-sync. Verify GC has only 1 remaining."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'KeepMe', 'DelTest')
        make_bb_contact(bbf, 'DeleteMe', 'DelTest')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
        self.assertTrue(result)
        self.assertEqual(count_gc_contacts(self.gc_folder), 2)

        # Delete one contact from BB
        bbdb, bbf = reopen_bb(BB_FILE)
        cons = bbf.find_contacts_by_name(name='DeleteMe')
        self.assertEqual(len(cons), 1)
        bbf.del_itemids([cons[0].get_itemid()])
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
        self.assertTrue(result)

        # Verify GC now has only 1 contact
        time.sleep(1)  # let Google propagate
        cnt = count_gc_contacts(self.gc_folder)
        self.assertEqual(cnt, 1, 'Expected 1 contact in GC, got %d' % cnt)

        # Verify the right one survived
        persons = self.gc_folder._get_group_contacts()
        names = [p.get('names', [{}])[0].get('givenName')
                 for p in persons]
        self.assertIn('KeepMe', names)
        self.assertNotIn('DeleteMe', names)

    ## -----------------------------------------------------------------
    ## Test 10: One-Way Sync Basic
    ## -----------------------------------------------------------------

    def test_j_sync1way_basic (self):
        """Create a contact in GC (source), sync 1-way. Verify it appears in BBDB (destination)."""
        config.set_sync_dir(PROFILE_NAME, 'SYNC1WAY')

        create_gc_contact(self.gcdb, self.test_gid,
                          'OneWayGC', 'Test', email='oneway@test.com')
        time.sleep(2)  # API propagation

        bbdb, bbf = open_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
        self.assertTrue(result)

        bbdb, bbf = reopen_bb(BB_FILE)
        self.assertEqual(len(bbf.get_contacts()), 1)
        names = [c.get_firstname() for c in bbf.get_contacts().values()]
        self.assertIn('OneWayGC', names)

    ## -----------------------------------------------------------------
    ## Test 11: One-Way Sync Ignores Destination Changes
    ## -----------------------------------------------------------------

    def test_k_sync1way_ignores_dst_changes (self):
        """After 1-way sync, add a contact in BBDB (destination). Re-sync.
        Verify Google Contacts (source) is unchanged."""
        config.set_sync_dir(PROFILE_NAME, 'SYNC1WAY')

        # 1. Sync one contact GC -> BB
        create_gc_contact(self.gcdb, self.test_gid,
                          'OneWayGC', 'Test')
        time.sleep(2)

        bbdb, bbf = open_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
        self.assertTrue(result)

        # 2. Add a new contact to BBDB (destination)
        bbdb, bbf = reopen_bb(BB_FILE)
        make_bb_contact(bbf, 'BBOnly', 'Contact')
        bbf.save()

        # 3. Re-sync 1-way
        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
        self.assertTrue(result)

        # 4. Verify Google Contacts (source) still has only 1 contact
        self.assertEqual(count_gc_contacts(self.gc_folder), 1)

    ## -----------------------------------------------------------------
    ## Test 12: Conflict Resolution - GC Wins
    ## -----------------------------------------------------------------

    def test_l_conflict_gc_wins (self):
        """Modify the same contact on both sides. GC (DB1) wins."""
        # 1. Initial sync of a contact
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'ConflictMe', 'TestGCBB', company='OldCorp')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
        self.assertTrue(result)
        self.assertEqual(count_gc_contacts(self.gc_folder), 1)

        # Retrieve the GC contact resource name
        persons = self.gc_folder._get_group_contacts()
        self.assertEqual(len(persons), 1)
        rname = persons[0].get('resourceName')
        self.assertIsNotNone(rname)

        time.sleep(5.1)  # Ensure timestamp beats last sync (takes care of GC clock skew tolerance)

        # 2. Modify BBDB contact
        bbdb, bbf = reopen_bb(BB_FILE)
        cons = bbf.find_contacts_by_name(name='ConflictMe')
        self.assertEqual(len(cons), 1)
        cons[0].set_company('BBDBCorp')
        bbf.save()

        # 3. Modify GC contact
        update_gc_contact_company(self.gcdb, rname, 'GCCorp')

        # 4. Set GC to win ('1')
        config.set_conflict_resolve(PROFILE_NAME, '1')

        # 5. Sync and verify GC version wins on both sides
        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
        self.assertTrue(result)

        # Verify BBDB updated to GC version ('GCCorp')
        bbdb, bbf = reopen_bb(BB_FILE)
        cons = bbf.find_contacts_by_name(name='ConflictMe')
        self.assertEqual(len(cons), 1)
        self.assertEqual(cons[0].get_company(), 'GCCorp')

        # Verify GC remains 'GCCorp'
        persons = self.gc_folder._get_group_contacts()
        self.assertEqual(len(persons), 1)
        self.assertEqual(persons[0].get('organizations', [{}])[0].get('name'), 'GCCorp')

    ## -----------------------------------------------------------------
    ## Test 13: Conflict Resolution - BB Wins
    ## -----------------------------------------------------------------

    def test_m_conflict_bb_wins (self):
        """Modify the same contact on both sides. BB (DB2) wins."""
        # 1. Initial sync of a contact
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'ConflictMe', 'TestGCBB', company='OldCorp')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
        self.assertTrue(result)
        self.assertEqual(count_gc_contacts(self.gc_folder), 1)

        # Retrieve the GC contact resource name
        persons = self.gc_folder._get_group_contacts()
        self.assertEqual(len(persons), 1)
        rname = persons[0].get('resourceName')
        self.assertIsNotNone(rname)

        time.sleep(5.1)  # Ensure timestamp beats last sync (takes care of GC clock skew tolerance)

        # 2. Modify BBDB contact
        bbdb, bbf = reopen_bb(BB_FILE)
        cons = bbf.find_contacts_by_name(name='ConflictMe')
        self.assertEqual(len(cons), 1)
        cons[0].set_company('BBDBCorp')
        bbf.save()

        # 3. Modify GC contact
        update_gc_contact_company(self.gcdb, rname, 'GCCorp')

        # 4. Set BB to win ('2')
        config.set_conflict_resolve(PROFILE_NAME, '2')

        # 5. Sync and verify BB version wins on both sides
        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
        self.assertTrue(result)

        # Verify BBDB remains 'BBDBCorp'
        bbdb, bbf = reopen_bb(BB_FILE)
        cons = bbf.find_contacts_by_name(name='ConflictMe')
        self.assertEqual(len(cons), 1)
        self.assertEqual(cons[0].get_company(), 'BBDBCorp')

        # Verify GC updated to BB version ('BBDBCorp')
        time.sleep(1.5)  # Let Google API propagate update
        persons = self.gc_folder._get_group_contacts()
        self.assertEqual(len(persons), 1)
        self.assertEqual(persons[0].get('organizations', [{}])[0].get('name'), 'BBDBCorp')

    ## -----------------------------------------------------------------
    ## Test 14: Bidirectional Additions
    ## -----------------------------------------------------------------

    def test_n_bidirectional_new (self):
        """Add new contacts on both sides independently, sync, verify."""
        # 1. Create a contact on BBDB
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'BBNew', 'Contact')
        bbf.save()

        # 2. Create a contact on Google Contacts
        create_gc_contact(self.gcdb, self.test_gid, 'GCNew', 'Contact')
        time.sleep(2)

        # 3. Sync
        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
        self.assertTrue(result)

        # 4. Verify both exist in BBDB
        bbdb, bbf = reopen_bb(BB_FILE)
        self.assertEqual(len(bbf.get_contacts()), 2)
        bb_names = sorted([c.get_firstname() for c in bbf.get_contacts().values()])
        self.assertEqual(bb_names, ['BBNew', 'GCNew'])

        # 5. Verify both exist in Google Contacts
        self.assertEqual(count_gc_contacts(self.gc_folder), 2)
        persons = self.gc_folder._get_group_contacts()
        gc_names = sorted([p.get('names', [{}])[0].get('givenName') for p in persons])
        self.assertEqual(gc_names, ['BBNew', 'GCNew'])

    ## -----------------------------------------------------------------
    ## Test 15: Unicode Support
    ## -----------------------------------------------------------------

    def test_o_unicode (self):
        """Create BB contacts with Unicode names, sync, verify GC fields."""
        bbdb, bbf = open_bb(BB_FILE)
        make_bb_contact(bbf, 'Héctor', 'Muñoz')
        make_bb_contact(bbf, '太郎', '山田')
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
        self.assertTrue(result)

        # Verify Google Contacts has both with correct names
        self.assertEqual(count_gc_contacts(self.gc_folder), 2)
        persons = self.gc_folder._get_group_contacts()
        gc_names = sorted([p.get('names', [{}])[0].get('givenName') for p in persons])
        self.assertEqual(gc_names, ['Héctor', '太郎'])

    ## -----------------------------------------------------------------
    ## Test 16: Minimal/Empty Fields
    ## -----------------------------------------------------------------

    def test_p_empty_fields (self):
        """Sync a contact with only first name from BB to GC."""
        bbdb, bbf = open_bb(BB_FILE)
        con = BBContact(bbf)
        con.set_firstname('Minimalist')
        bbf.add_contact(con)
        bbf.save()

        bbdb, bbf = reopen_bb(BB_FILE)
        result = run_sync(config, PROFILE_NAME, self.gcdb, bbdb)
        self.assertTrue(result)

        # Verify Google Contacts has 1 contact named 'Minimalist'
        self.assertEqual(count_gc_contacts(self.gc_folder), 1)
        persons = self.gc_folder._get_group_contacts()
        self.assertEqual(persons[0].get('names', [{}])[0].get('givenName'), 'Minimalist')



## ---------------------------------------------------------------------------
## Main
## ---------------------------------------------------------------------------

def main ():
    global config, cs_file, gc_user

    best_effort = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], '',
                                   ['cs=', 'user=', 'best-effort'])
    except getopt.error as msg:
        print('Usage: python test_sync_gc_bb.py [--cs /path/to/creds.json] '
              '[--user label] [--best-effort]')
        sys.exit(2)

    for option, arg in opts:
        if option == '--cs':
            cs_file = os.path.abspath(arg)
        elif option == '--user':
            gc_user = arg
        elif option == '--best-effort':
            best_effort = True

    if cs_file and not os.path.exists(cs_file):
        print('ERROR: Client secrets file not found: %s' % cs_file)
        sys.exit(1)

    setup_user_dir()

    if not os.path.exists(GC_CREDS_DIR):
        os.makedirs(GC_CREDS_DIR)

    if cs_file:
        dest = os.path.join(GC_CREDS_DIR, os.path.basename(cs_file))
        if not os.path.exists(dest):
            shutil.copyfile(cs_file, dest)
        cs_file = dest
    else:
        jsons = [f for f in glob.glob(os.path.join(GC_CREDS_DIR, '*.json'))
                 if os.path.basename(f) not in ('state.json', 'config.json')]
        if jsons:
            cs_file = jsons[0]
            logging.info('Using cached client secrets: %s', cs_file)
        elif best_effort:
            logging.warning('No cached credentials in %s/ -- GC sync tests '
                            'will be skipped.', GC_CREDS_DIR)
            logging.warning('To enable: make sync-gc '
                            'GOOGLE_CL_SECRET=/path/to/client_secret.json')
        else:
            print('ERROR: No --cs provided and no cached credentials in %s/'
                  % GC_CREDS_DIR)
            print('First run requires:')
            print('  make sync-gc GOOGLE_CL_SECRET=/path/to/client_secret.json')
            sys.exit(1)

    config = Config(asynk_base_dir=ASYNK_BASE_DIR, user_dir=GC_CREDS_DIR)

    ## Discover all available Google test accounts for round-robin
    global _gc_accounts
    _gc_accounts = discover_gc_accounts(GC_CREDS_DIR)
    if len(_gc_accounts) > 1:
        logging.info('Multi-account mode: %d accounts available (%s)',
                     len(_gc_accounts), ', '.join(_gc_accounts))
    elif _gc_accounts:
        logging.info('Single account mode: %s', _gc_accounts[0])

    sys.argv = [sys.argv[0]] + args
    unittest.main(verbosity=2)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()
