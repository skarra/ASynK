# -*- coding: utf-8 -*-
##
## Created : Tue May 19 23:45:00 PDT 2026
## SPDX-FileCopyrightText: 2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
#####
##
## Gold tests for the ASynK sync engine using Google Contacts <-> Google Contacts.
## Requires live Google credentials — runs best-effort when invoked via
## 'make all', hard error when invoked via 'make sync-gc-gc'.
##
## Usage: python test_sync_gc_gc.py [--cs /path/to/creds.json]
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
from sync        import Sync

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------

ASYNK_BASE_DIR = DIR_PATH
USER_DIR       = os.path.abspath(os.path.join(CUR_DIR, 'user_dir_gc_gc'))
STATE_SRC      = os.path.join(DIR_PATH, 'state.init.json')
CONF_SRC       = os.path.join(DIR_PATH, 'config', 'config_v6.json')

GC_CREDS_DIR   = os.path.abspath(os.path.join(CUR_DIR, 'gc_creds'))

PROFILE_NAME   = 'testgcgc'
TEST_GROUP     = 'ASynK GC-GC Test (safe to delete)'

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

def print_test_banner(test_name, account1, account2, idx1, idx2):
    print('\n' + '-'*80)
    print('>> RUNNING TEST: %s' % test_name)
    print('>> USING ACCOUNTS: %s (Pool: %d) <-> %s (Pool: %d)' % (account1, idx1, account2, idx2))
    print('-'*80)

def setup_user_dir ():
    if os.path.exists(USER_DIR):
        shutil.rmtree(USER_DIR)
    os.makedirs(USER_DIR)
    shutil.copyfile(STATE_SRC, os.path.join(USER_DIR, 'state.json'))
    shutil.copyfile(CONF_SRC, os.path.join(USER_DIR, 'config.json'))

def create_profile (conf, pname, gc_fid1, gc_fid2):
    """Create a sync profile for gc<->gc."""
    profile = conf.get_profile_defaults()
    profile.update({
        'coll_1': {'dbid': 'gc', 'stid': None, 'foid': gc_fid1},
        'coll_2': {'dbid': 'gc', 'stid': None, 'foid': gc_fid2},
        'olgid': None,
        'sync_dir': 'SYNC2WAY',
        'sync_state': None,
        'conflict_resolve': '1',
    })
    conf.add_profile(pname, profile)

def run_sync (conf, pname, gcdb1, gcdb2, dirn=None):
    """Run a sync between two GC PIMDBs."""
    startt = conf.get_curr_time()
    sync = Sync(conf, pname, [gcdb1, gcdb2])
    if not dirn:
        dirn = conf.get_sync_dir(pname)
    result = sync.sync(dirn)
    if result:
        conf.set_last_sync_start(pname, val=startt)
        conf.set_last_sync_stop(pname)
        sync.save_item_lists()
    return result

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

class TestSyncGCGC(unittest.TestCase):
    """GC <-> GC sync engine integration tests.

    Uses a pool of Google accounts. For each test, we rotate and select a
    distinct pair of accounts to run GC-to-GC synchronization.
    """

    @classmethod
    def setUpClass (cls):
        print_suite_banner(cls.__name__)
        if cs_file is None:
            raise unittest.SkipTest(
                'No credentials available; skipping GC-to-GC sync tests.')

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

            ## Each account gets its own test group
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

        if len(cls._account_pool) < 2:
            raise unittest.SkipTest(
                'At least two working Google accounts are required for GC-to-GC tests.')

        logging.info('Account pool ready: %d account(s)', len(cls._account_pool))
        cls._pool_idx = 0

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
        """Rotate to next pair of accounts, clean contacts, create profile."""
        import gc as _gc
        _gc.collect()

        ## Rotate to next pair of accounts
        pool = self.__class__._account_pool
        idx1 = self.__class__._pool_idx % len(pool)
        self.__class__._pool_idx += 1
        idx2 = (idx1 + 1) % len(pool)

        label1, gcdb1, gc_folder1, test_gid1 = pool[idx1]
        label2, gcdb2, gc_folder2, test_gid2 = pool[idx2]

        self.gcdb1 = gcdb1
        self.gc_folder1 = gc_folder1
        self.test_gid1 = test_gid1

        self.gcdb2 = gcdb2
        self.gc_folder2 = gc_folder2
        self.test_gid2 = test_gid2

        print_test_banner(self._testMethodName, label1, label2, idx1, idx2)

        cleanup_gc_contacts(self.gc_folder1, self.gcdb1)
        cleanup_gc_contacts(self.gc_folder2, self.gcdb2)

        self.gc_folder1.reset_contacts()
        self.gc_folder2.reset_contacts()
        time.sleep(2)  # Let Google propagate deletes

        ## Reset state.json within GC_CREDS_DIR to clear stale item lists
        ## and profile data, but preserve credentials and config.
        shutil.copyfile(STATE_SRC, os.path.join(GC_CREDS_DIR, 'state.json'))

        global config
        config = Config(asynk_base_dir=ASYNK_BASE_DIR, user_dir=GC_CREDS_DIR)

        self.gcdb1.set_config(config)
        self.gc_folder1.set_config(config)
        self.gcdb2.set_config(config)
        self.gc_folder2.set_config(config)

        ## Recreate user_dir to wipe local db config state
        setup_user_dir()

        ## Build sync profile for gc1 <-> gc2
        create_profile(config, PROFILE_NAME, self.test_gid1, self.test_gid2)
        time.sleep(1)

    ## -----------------------------------------------------------------
    ## Test 1: Simple 2-Way Sync (Syncing new contact from GC1 to GC2)
    ## -----------------------------------------------------------------

    def test_a_sync_gc1_to_gc2 (self):
        """Add new contact on GC1, sync, verify on GC2."""
        create_gc_contact(self.gcdb1, self.test_gid1, 'Alice', 'Smith', 'alice@example.com', '111-222-3333')
        time.sleep(1.5)

        result = run_sync(config, PROFILE_NAME, self.gcdb1, self.gcdb2)
        self.assertTrue(result)

        # Verify GC2 has 1 contact
        self.assertEqual(count_gc_contacts(self.gc_folder2), 1)
        persons = self.gc_folder2._get_group_contacts()
        self.assertEqual(persons[0].get('names', [{}])[0].get('givenName'), 'Alice')
        self.assertEqual(persons[0].get('emailAddresses', [{}])[0].get('value'), 'alice@example.com')

    ## -----------------------------------------------------------------
    ## Test 2: Simple 2-Way Sync (Syncing new contact from GC2 to GC1)
    ## -----------------------------------------------------------------

    def test_b_sync_gc2_to_gc1 (self):
        """Add new contact on GC2, sync, verify on GC1."""
        create_gc_contact(self.gcdb2, self.test_gid2, 'Bob', 'Jones', 'bob@example.com', '444-555-6666')
        time.sleep(1.5)

        result = run_sync(config, PROFILE_NAME, self.gcdb1, self.gcdb2)
        self.assertTrue(result)

        # Verify GC1 has 1 contact
        self.assertEqual(count_gc_contacts(self.gc_folder1), 1)
        persons = self.gc_folder1._get_group_contacts()
        self.assertEqual(persons[0].get('names', [{}])[0].get('givenName'), 'Bob')
        self.assertEqual(persons[0].get('emailAddresses', [{}])[0].get('value'), 'bob@example.com')

    ## -----------------------------------------------------------------
    ## Test 3: Bidirectional New Contacts
    ## -----------------------------------------------------------------

    def test_c_bidirectional_new (self):
        """Add new contacts on both sides independently, sync, verify."""
        create_gc_contact(self.gcdb1, self.test_gid1, 'Alice', 'Smith')
        create_gc_contact(self.gcdb2, self.test_gid2, 'Bob', 'Jones')
        time.sleep(2.5)

        result = run_sync(config, PROFILE_NAME, self.gcdb1, self.gcdb2)
        self.assertTrue(result)

        # Both sides should now have 2 contacts
        self.assertEqual(count_gc_contacts(self.gc_folder1), 2)
        self.assertEqual(count_gc_contacts(self.gc_folder2), 2)

        names1 = sorted([p.get('names', [{}])[0].get('givenName') for p in self.gc_folder1._get_group_contacts()])
        names2 = sorted([p.get('names', [{}])[0].get('givenName') for p in self.gc_folder2._get_group_contacts()])
        self.assertEqual(names1, ['Alice', 'Bob'])
        self.assertEqual(names2, ['Alice', 'Bob'])

    ## -----------------------------------------------------------------
    ## Test 4: Modifying existing contact on GC1 -> syncs to GC2
    ## -----------------------------------------------------------------

    def test_d_update_gc1_to_gc2 (self):
        """Modify contact on GC1, sync, verify updated on GC2."""
        rname = create_gc_contact(self.gcdb1, self.test_gid1, 'Alice', 'Smith')
        time.sleep(1.5)

        result = run_sync(config, PROFILE_NAME, self.gcdb1, self.gcdb2)
        self.assertTrue(result)
        self.assertEqual(count_gc_contacts(self.gc_folder2), 1)

        # Clock skew tolerance buffer
        time.sleep(5.1)

        # Modify on GC1
        update_gc_contact_company(self.gcdb1, rname, 'AliceCorp')

        # Sync
        result = run_sync(config, PROFILE_NAME, self.gcdb1, self.gcdb2)
        self.assertTrue(result)

        # Verify GC2 updated
        persons = self.gc_folder2._get_group_contacts()
        self.assertEqual(persons[0].get('organizations', [{}])[0].get('name'), 'AliceCorp')

    ## -----------------------------------------------------------------
    ## Test 5: Modifying existing contact on GC2 -> syncs to GC1
    ## -----------------------------------------------------------------

    def test_e_update_gc2_to_gc1 (self):
        """Modify contact on GC2, sync, verify updated on GC1."""
        rname2 = create_gc_contact(self.gcdb2, self.test_gid2, 'Bob', 'Jones')
        time.sleep(1.5)

        result = run_sync(config, PROFILE_NAME, self.gcdb1, self.gcdb2)
        self.assertTrue(result)
        self.assertEqual(count_gc_contacts(self.gc_folder1), 1)

        # Clock skew tolerance buffer
        time.sleep(5.1)

        # Modify on GC2
        update_gc_contact_company(self.gcdb2, rname2, 'BobCorp')

        # Sync
        result = run_sync(config, PROFILE_NAME, self.gcdb1, self.gcdb2)
        self.assertTrue(result)

        # Verify GC1 updated
        persons = self.gc_folder1._get_group_contacts()
        self.assertEqual(persons[0].get('organizations', [{}])[0].get('name'), 'BobCorp')

    ## -----------------------------------------------------------------
    ## Test 6: Conflict Resolution - GC1 wins
    ## -----------------------------------------------------------------

    def test_f_conflict_gc1_wins (self):
        """Conflicting updates. GC1 (Collection 1) wins."""
        # 1. Sync contact initially
        rname1 = create_gc_contact(self.gcdb1, self.test_gid1, 'ConflictMe', 'Smith', email='test@example.com')
        time.sleep(1.5)

        result = run_sync(config, PROFILE_NAME, self.gcdb1, self.gcdb2)
        self.assertTrue(result)

        persons2 = self.gc_folder2._get_group_contacts()
        self.assertEqual(len(persons2), 1)
        rname2 = persons2[0].get('resourceName')

        # 2. Wait to avoid timestamp collision
        time.sleep(5.1)

        # 3. Apply conflicting changes
        update_gc_contact_company(self.gcdb1, rname1, 'Corp1')
        update_gc_contact_company(self.gcdb2, rname2, 'Corp2')

        # Set conflict resolution to Collection 1 ('1')
        config.set_conflict_resolve(PROFILE_NAME, '1')

        # 4. Sync
        result = run_sync(config, PROFILE_NAME, self.gcdb1, self.gcdb2)
        self.assertTrue(result)

        # 5. Verify Corp1 wins on both sides
        time.sleep(1.5)
        persons1 = self.gc_folder1._get_group_contacts()
        persons2 = self.gc_folder2._get_group_contacts()
        self.assertEqual(persons1[0].get('organizations', [{}])[0].get('name'), 'Corp1')
        self.assertEqual(persons2[0].get('organizations', [{}])[0].get('name'), 'Corp1')

    ## -----------------------------------------------------------------
    ## Test 7: Conflict Resolution - GC2 wins
    ## -----------------------------------------------------------------

    def test_g_conflict_gc2_wins (self):
        """Conflicting updates. GC2 (Collection 2) wins."""
        # 1. Sync contact initially
        rname1 = create_gc_contact(self.gcdb1, self.test_gid1, 'ConflictMe', 'Smith', email='test@example.com')
        time.sleep(1.5)

        result = run_sync(config, PROFILE_NAME, self.gcdb1, self.gcdb2)
        self.assertTrue(result)

        persons2 = self.gc_folder2._get_group_contacts()
        self.assertEqual(len(persons2), 1)
        rname2 = persons2[0].get('resourceName')

        # 2. Wait to avoid timestamp collision
        time.sleep(5.1)

        # 3. Apply conflicting changes
        update_gc_contact_company(self.gcdb1, rname1, 'Corp1')
        update_gc_contact_company(self.gcdb2, rname2, 'Corp2')

        # Set conflict resolution to Collection 2 ('2')
        config.set_conflict_resolve(PROFILE_NAME, '2')

        # 4. Sync
        result = run_sync(config, PROFILE_NAME, self.gcdb1, self.gcdb2)
        self.assertTrue(result)

        # 5. Verify Corp2 wins on both sides
        time.sleep(1.5)
        persons1 = self.gc_folder1._get_group_contacts()
        persons2 = self.gc_folder2._get_group_contacts()
        self.assertEqual(persons1[0].get('organizations', [{}])[0].get('name'), 'Corp2')
        self.assertEqual(persons2[0].get('organizations', [{}])[0].get('name'), 'Corp2')

    ## -----------------------------------------------------------------
    ## Test 8: One-Way Sync GC1 -> GC2 (Basic propagation)
    ## -----------------------------------------------------------------

    def test_h_sync1way_basic (self):
        """Under SYNC1WAY, propagate GC1 addition to GC2."""
        config.set_sync_dir(PROFILE_NAME, 'SYNC1WAY')
        create_gc_contact(self.gcdb1, self.test_gid1, 'Alice', 'Smith')
        time.sleep(1.5)

        result = run_sync(config, PROFILE_NAME, self.gcdb1, self.gcdb2)
        self.assertTrue(result)

        # Verify GC2 has Alice
        self.assertEqual(count_gc_contacts(self.gc_folder2), 1)
        persons = self.gc_folder2._get_group_contacts()
        self.assertEqual(persons[0].get('names', [{}])[0].get('givenName'), 'Alice')

    ## -----------------------------------------------------------------
    ## Test 9: One-Way Sync GC1 -> GC2 (Ignores modifications on GC2)
    ## -----------------------------------------------------------------

    def test_i_sync1way_ignores_dst_changes (self):
        """Under SYNC1WAY, verify additions on GC2 do not sync back."""
        config.set_sync_dir(PROFILE_NAME, 'SYNC1WAY')

        # Sync GC1 Alice to GC2
        create_gc_contact(self.gcdb1, self.test_gid1, 'Alice', 'Smith')
        time.sleep(1.5)
        result = run_sync(config, PROFILE_NAME, self.gcdb1, self.gcdb2)
        self.assertTrue(result)

        # Add Bob to GC2
        create_gc_contact(self.gcdb2, self.test_gid2, 'Bob', 'Jones')
        time.sleep(1.5)

        # Sync again
        result = run_sync(config, PROFILE_NAME, self.gcdb1, self.gcdb2)
        self.assertTrue(result)

        # GC1 should only have Alice (Bob is ignored)
        self.assertEqual(count_gc_contacts(self.gc_folder1), 1)
        persons1 = self.gc_folder1._get_group_contacts()
        self.assertEqual(persons1[0].get('names', [{}])[0].get('givenName'), 'Alice')

    ## -----------------------------------------------------------------
    ## Test 10: Deletion from GC1 propagates to GC2
    ## -----------------------------------------------------------------

    def test_j_del_gc1_to_gc2 (self):
        """Delete contact on GC1 -> verify deleted on GC2."""
        rname1 = create_gc_contact(self.gcdb1, self.test_gid1, 'Alice', 'Smith')
        time.sleep(1.5)

        result = run_sync(config, PROFILE_NAME, self.gcdb1, self.gcdb2)
        self.assertTrue(result)
        self.assertEqual(count_gc_contacts(self.gc_folder2), 1)

        # Delete on GC1
        delete_gc_contact(self.gcdb1, rname1)
        time.sleep(1.5)

        # Sync
        result = run_sync(config, PROFILE_NAME, self.gcdb1, self.gcdb2)
        self.assertTrue(result)

        # Verify deleted from GC2
        self.assertEqual(count_gc_contacts(self.gc_folder2), 0)

    ## -----------------------------------------------------------------
    ## Test 11: Deletion from GC2 propagates to GC1 (fixes key bug)
    ## -----------------------------------------------------------------

    def test_k_del_gc2_to_gc1 (self):
        """Delete contact on GC2 -> verify deleted on GC1."""
        rname1 = create_gc_contact(self.gcdb1, self.test_gid1, 'Alice', 'Smith')
        time.sleep(1.5)

        result = run_sync(config, PROFILE_NAME, self.gcdb1, self.gcdb2)
        self.assertTrue(result)
        self.assertEqual(count_gc_contacts(self.gc_folder1), 1)

        # Retrieve resource name on GC2
        persons2 = self.gc_folder2._get_group_contacts()
        self.assertEqual(len(persons2), 1)
        rname2 = persons2[0].get('resourceName')

        # Delete on GC2
        delete_gc_contact(self.gcdb2, rname2)
        time.sleep(1.5)

        # Sync
        result = run_sync(config, PROFILE_NAME, self.gcdb1, self.gcdb2)
        self.assertTrue(result)

        # Verify deleted from GC1
        self.assertEqual(count_gc_contacts(self.gc_folder1), 0)

    ## -----------------------------------------------------------------
    ## Test 12: Unicode Support
    ## -----------------------------------------------------------------

    def test_l_unicode (self):
        """Verify sync of Unicode names."""
        create_gc_contact(self.gcdb1, self.test_gid1, 'Héctor', 'Muñoz')
        create_gc_contact(self.gcdb1, self.test_gid1, '太郎', '山田')
        time.sleep(2)

        result = run_sync(config, PROFILE_NAME, self.gcdb1, self.gcdb2)
        self.assertTrue(result)

        # Verify GC2 has both with correct names
        self.assertEqual(count_gc_contacts(self.gc_folder2), 2)
        persons = self.gc_folder2._get_group_contacts()
        gc_names = sorted([p.get('names', [{}])[0].get('givenName') for p in persons])
        self.assertEqual(gc_names, ['Héctor', '太郎'])

    ## -----------------------------------------------------------------
    ## Test 13: Minimal/Empty Fields
    ## -----------------------------------------------------------------

    def test_m_empty_fields (self):
        """Sync a contact with only first name from GC1 to GC2."""
        create_gc_contact(self.gcdb1, self.test_gid1, 'Minimalist', '')
        time.sleep(1.5)

        result = run_sync(config, PROFILE_NAME, self.gcdb1, self.gcdb2)
        self.assertTrue(result)

        # Verify GC2 has Alice
        self.assertEqual(count_gc_contacts(self.gc_folder2), 1)
        persons = self.gc_folder2._get_group_contacts()
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
        print('Usage: python test_sync_gc_gc.py [--cs /path/to/creds.json] '
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
            logging.warning('To enable: make sync-gc-gc '
                            'GOOGLE_CL_SECRET=/path/to/client_secret.json')
        else:
            print('ERROR: No --cs provided and no cached credentials in %s/'
                  % GC_CREDS_DIR)
            print('First run requires:')
            print('  make sync-gc-gc GOOGLE_CL_SECRET=/path/to/client_secret.json')
            sys.exit(1)

    config = Config(asynk_base_dir=ASYNK_BASE_DIR, user_dir=GC_CREDS_DIR)

    ## Discover all available Google test accounts
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
