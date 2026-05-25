##
## Created : Thu May 15 20:14:00 PDT 2026
## SPDX-FileCopyrightText: 2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
## ####
##
## Integration tests for the Google Contacts (GC) connector using the
## People API v1.  These tests require real Google credentials.
##
## Prerequisites:
##   1. A Google Cloud project with the People API enabled
##   2. An OAuth2 client secrets file (credentials.json)
##   3. Run with:
##        make gc GOOGLE_CL_SECRET=~/path/to/credentials.json
##      or:
##        python test_gc.py --cs ~/path/to/credentials.json
##
##   On first run, a browser window will open for OAuth consent.
##   Subsequent runs reuse the cached token.
##

import getopt, glob, logging, os, os.path, shutil, sys, unittest

## Fix sys.path so we can import asynk modules
DIR_PATH    = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath('__file__')), '../..'))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk')]
sys.path = EXTRA_PATHS + sys.path

from state    import Config
from pimdb_gc import GCPIMDB, GCContactsFolder

## Directories
user_dir     = os.path.abspath('user_dir')
gc_creds_dir = os.path.abspath('gc_creds')  # persistent — survives 'make clean'
state_src    = os.path.join('.', 'state.test.json')
state_dest   = os.path.join(user_dir, 'state.json')
confn_src    = os.path.join('..', '..', 'config', 'config_v4.json')
confn_dest   = os.path.join(user_dir, 'config.json')

## These get filled in by main()
config    = None
cs_file   = None   # path to OAuth2 client secrets JSON
gc_user   = 'test' # label for the token file

def setup_user_dir ():
    """Create (or re-create) a clean user_dir with state + config files."""
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)
    os.makedirs(user_dir)
    shutil.copyfile(state_src, state_dest)
    if os.path.exists(confn_src):
        shutil.copyfile(confn_src, confn_dest)

def setup_gc_creds_dir ():
    """Ensure the persistent gc_creds/ directory exists.  Unlike user_dir/,
    this is NOT wiped on each run — it stores the OAuth2 client secrets
    and cached tokens across test runs."""
    if not os.path.exists(gc_creds_dir):
        os.makedirs(gc_creds_dir)

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

def print_suite_banner(suite_name):
    print('\n' + '='*80)
    print('>>> INITIALIZING TEST SUITE: %s' % suite_name)
    print('='*80)

def print_test_banner(test_name, account, pool_idx):
    print('\n' + '-'*80)
    print('>> RUNNING TEST: %s' % test_name)
    print('>> USING ACCOUNT: %s (Pool index: %d)' % (account, pool_idx))
    print('-'*80)

## ---------------------------------------------------------------------------
## Test cases
## ---------------------------------------------------------------------------

class TestGCAuth(unittest.TestCase):
    """Test that we can authenticate and create a GCPIMDB instance."""

    @classmethod
    def setUpClass (cls):
        """Build a pool of GCPIMDB instances for per-test rotation."""
        print_suite_banner(cls.__name__)
        if cs_file is None:
            raise unittest.SkipTest(
                'No credentials available; skipping GC tests.')

        cls._pimdb_pool = []
        for label in _get_account_labels():
            try:
                pimdb = GCPIMDB(config, label, cs_file)
                cls._pimdb_pool.append((label, pimdb))
            except Exception as e:
                logging.warning('Skipping account %s: %s', label, e)
        if not cls._pimdb_pool:
            raise unittest.SkipTest('No working Google accounts')
        cls._pool_idx = 0

    def setUp (self):
        pool = self.__class__._pimdb_pool
        idx = self.__class__._pool_idx % len(pool)
        self.__class__._pool_idx += 1
        self._gc_user, self.pimdb = pool[idx]
        print_test_banner(self._testMethodName, self._gc_user, idx)

    def test_service_exists (self):
        """After init, the People API service object should be set."""
        svc = self.pimdb.get_service()
        self.assertIsNotNone(svc)

    def test_dbid (self):
        """The database ID for Google Contacts is 'gc'."""
        self.assertEqual(self.pimdb.get_dbid(), 'gc')

    def test_user (self):
        """The user label should match what was passed to __init__."""
        self.assertEqual(self.pimdb.get_user(), self._gc_user)

class TestGCGroups(unittest.TestCase):
    """Test contact group operations via the People API."""

    @classmethod
    def setUpClass (cls):
        print_suite_banner(cls.__name__)
        if cs_file is None:
            raise unittest.SkipTest(
                'No credentials available; skipping GC tests.')
        cls._pimdb_pool = []
        for label in _get_account_labels():
            try:
                pimdb = GCPIMDB(config, label, cs_file)
                cls._pimdb_pool.append((label, pimdb))
            except Exception as e:
                logging.warning('Skipping account %s: %s', label, e)
        if not cls._pimdb_pool:
            raise unittest.SkipTest('No working Google accounts')
        cls._pool_idx = 0

    def setUp (self):
        pool = self.__class__._pimdb_pool
        idx = self.__class__._pool_idx % len(pool)
        self.__class__._pool_idx += 1
        self._gc_user, self.pimdb = pool[idx]
        print_test_banner(self._testMethodName, self._gc_user, idx)

    def test_list_folders (self):
        """list_folders should return a non-empty list (every account has
        at least the system groups)."""
        folders = self.pimdb.list_folders(silent=True)
        self.assertIsInstance(folders, list)
        self.assertGreater(len(folders), 0)

    def test_list_folders_tuple_format (self):
        """Each entry from list_folders should be a (resourceName, name,
        group_resource) tuple."""
        folders = self.pimdb.list_folders(silent=True)
        for f in folders:
            self.assertEqual(len(f), 3)
            resource_name, name, group = f
            self.assertTrue(resource_name.startswith('contactGroups/'))

    def test_list_folders_verbose (self):
        """List all folders with names and IDs.  Always passes if the API
        call succeeds; the printed output is useful for interactive runs."""
        folders = self.pimdb.list_folders(silent=True)
        self.assertGreater(len(folders), 0)
        print('\n  %-4s %-35s %s' % ('#', 'Name', 'Resource ID'))
        print('  ' + '-' * 75)
        for i, (rid, name, _group) in enumerate(folders, 1):
            print('  %-4d %-35s %s' % (i, name, rid))

    @unittest.skipUnless(GCContactsFolder, 'GCContactsFolder not yet migrated')
    def test_default_folder_set (self):
        """After init, the default contacts folder should be
        contactGroups/myContacts."""
        df = self.pimdb.get_def_folder()
        self.assertIsNotNone(df)
        self.assertEqual(df.get_itemid(), 'contactGroups/myContacts')

    def test_find_group_my_contacts (self):
        """find_group should locate 'myContacts' by name."""
        rid = self.pimdb.find_group('myContacts')
        self.assertIsNotNone(rid)
        self.assertTrue(rid.startswith('contactGroups/'))

    @unittest.skipUnless(GCContactsFolder, 'GCContactsFolder not yet migrated')
    def test_create_and_delete_group (self):
        """Create a test group, verify it exists, then delete it."""
        test_name = 'ASynK Test Group (safe to delete)'

        # Create
        gid = self.pimdb.new_folder(test_name)
        self.assertIsNotNone(gid)
        self.assertTrue(gid.startswith('contactGroups/'))

        # Verify it can be found
        found = self.pimdb.find_group(test_name)
        self.assertEqual(found, gid)

        # Delete
        self.pimdb.del_folder(gid)

        # Verify it's gone (retry — Google API is eventually consistent)
        import time
        found = gid   # assume still there
        for _ in range(5):
            time.sleep(2)
            found = self.pimdb.find_group(test_name)
            if found is None:
                break
        self.assertIsNone(found)

class TestGCContacts(unittest.TestCase):
    """Test contact-level operations via the People API.

    Tests b, c, d form a chain (create -> update -> delete) that shares
    a contact resource, so they are pinned to the same account.  Tests
    a and e are independent and rotate freely."""

    TEST_GROUP_NAME = 'ASynK Test Contacts (safe to delete)'

    ## Tests that must share the same account (they pass _created_rid)
    _CHAINED_TESTS = {'test_b_create_and_read_contact',
                      'test_c_update_contact',
                      'test_d_delete_contact'}

    @classmethod
    def setUpClass (cls):
        print_suite_banner(cls.__name__)
        if cs_file is None:
            raise unittest.SkipTest(
                'No credentials available; skipping GC tests.')

        ## Build pool of (label, pimdb, test_gid, test_folder)
        cls._pimdb_pool = []
        labels = _get_account_labels()
        for label in labels:
            try:
                pimdb = GCPIMDB(config, label, cs_file)
            except Exception as e:
                logging.warning('Skipping account %s: %s', label, e)
                continue

            group_name = cls.TEST_GROUP_NAME if len(labels) == 1 \
                         else '%s (%s)' % (cls.TEST_GROUP_NAME, label)
            test_gid = pimdb.new_folder(group_name)
            test_folder = None
            for f in pimdb.get_contacts_folders():
                if f.get_itemid() == test_gid:
                    test_folder = f
                    break
            if test_folder is None:
                logging.warning('Could not find test group for %s', label)
                continue

            cls._pimdb_pool.append((label, pimdb, test_gid, test_folder))

        if not cls._pimdb_pool:
            raise unittest.SkipTest('No working Google accounts')
        cls._pool_idx = 0

        ## Pin account 0 for the chained tests (b/c/d)
        cls._chain_label, cls._chain_pimdb, cls._chain_gid, \
            cls._chain_folder = cls._pimdb_pool[0]

    @classmethod
    def tearDownClass (cls):
        """Clean up: delete all test groups."""
        import time
        for label, pimdb, test_gid, test_folder in \
                getattr(cls, '_pimdb_pool', []):
            try:
                pimdb.del_folder(test_gid)
            except Exception as e:
                logging.warning('Cleanup failed for %s: %s', label, e)
        time.sleep(2)

    def setUp (self):
        """Pick account: chained tests (b/c/d) use the pinned account;
        independent tests rotate through the pool."""
        if self._testMethodName in self._CHAINED_TESTS:
            self._gc_user = self._chain_label
            self.pimdb = self._chain_pimdb
            self.test_gid = self._chain_gid
            self.test_folder = self._chain_folder
            print_test_banner(self._testMethodName, self._gc_user, 0)
        else:
            pool = self.__class__._pimdb_pool
            idx = self.__class__._pool_idx % len(pool)
            self.__class__._pool_idx += 1
            self._gc_user, self.pimdb, self.test_gid, self.test_folder = \
                pool[idx]
            print_test_banner(self._testMethodName, self._gc_user, idx)

    def test_a_list_contacts_in_folder (self):
        """Listing contacts in a freshly created group should return
        an empty list."""
        persons = self.test_folder._get_group_contacts()
        self.assertIsInstance(persons, list)
        self.assertEqual(len(persons), 0)

    def test_b_create_and_read_contact (self):
        """Create a contact via the People API and read it back."""
        svc = self.pimdb.get_service()

        person = svc.people().createContact(
            body={
                'names': [{'givenName': 'TestFirst',
                           'familyName': 'TestLast'}],
                'emailAddresses': [{'value': 'test@example.com',
                                    'type': 'work'}],
                'phoneNumbers': [{'value': '+1-555-0100',
                                  'type': 'mobile'}],
                'memberships': [{
                    'contactGroupMembership': {
                        'contactGroupResourceName': self.test_gid
                    }
                }],
            },
            personFields='names,emailAddresses,phoneNumbers,memberships,metadata'
        ).execute()

        self.assertIn('resourceName', person)
        rid = person['resourceName']
        self.assertTrue(rid.startswith('people/'))

        ## Read it back
        fetched = svc.people().get(
            resourceName=rid,
            personFields='names,emailAddresses,phoneNumbers'
        ).execute()

        names = fetched.get('names', [])
        self.assertTrue(len(names) > 0)
        self.assertEqual(names[0].get('givenName'), 'TestFirst')
        self.assertEqual(names[0].get('familyName'), 'TestLast')

        emails = fetched.get('emailAddresses', [])
        self.assertTrue(len(emails) > 0)
        self.assertEqual(emails[0].get('value'), 'test@example.com')

        phones = fetched.get('phoneNumbers', [])
        self.assertTrue(len(phones) > 0)

        ## Save for subsequent tests
        self.__class__._created_rid = rid
        self.__class__._created_etag = fetched.get('etag')

    def test_c_update_contact (self):
        """Update the previously created contact's name."""
        rid = getattr(self.__class__, '_created_rid', None)
        if not rid:
            self.skipTest('No contact created in previous test')

        svc = self.pimdb.get_service()

        ## Fetch fresh to get current etag
        current = svc.people().get(
            resourceName=rid,
            personFields='names,metadata'
        ).execute()

        current['names'] = [{'givenName': 'UpdatedFirst',
                             'familyName': 'UpdatedLast'}]

        updated = svc.people().updateContact(
            resourceName=rid,
            body=current,
            updatePersonFields='names',
            personFields='names'
        ).execute()

        self.assertEqual(updated['names'][0]['givenName'], 'UpdatedFirst')
        self.assertEqual(updated['names'][0]['familyName'], 'UpdatedLast')

    def test_d_delete_contact (self):
        """Delete the previously created contact."""
        rid = getattr(self.__class__, '_created_rid', None)
        if not rid:
            self.skipTest('No contact created in previous test')

        svc = self.pimdb.get_service()
        svc.people().deleteContact(resourceName=rid).execute()

        ## Verify it's gone
        import time
        time.sleep(2)
        try:
            svc.people().get(
                resourceName=rid,
                personFields='names'
            ).execute()
            self.fail('Contact should have been deleted')
        except Exception:
            pass   # expected — 404 or similar

    def _populate_rich_contact (self, gc):
        gc.set_firstname('RoundFirst')
        gc.set_lastname('RoundLast')
        gc.set_middlename('M')
        gc.set_prefix('Dr')
        gc.set_suffix('Jr')
        gc.set_nickname('Roundy')
        gc.add_email_work('round@example.com')
        gc.set_email_prim('round@example.com')
        gc.add_phone_mob(('Mobile', '+1-555-0199'))
        gc.set_company('TestCorp')
        gc.set_title('Engineer')
        gc.set_dept('R&D')
        gc.set_birthday('1990-06-15')
        gc.add_web_home('https://example.com')

    def _verify_rich_contact_fields (self, gc_obj):
        ## Verify names & prefixes
        self.assertEqual(gc_obj.get_firstname(), 'RoundFirst')
        self.assertEqual(gc_obj.get_lastname(), 'RoundLast')
        self.assertEqual(gc_obj.get_middlename(), 'M')
        self.assertEqual(gc_obj.get_prefix(), 'Dr')
        self.assertEqual(gc_obj.get_suffix(), 'Jr')

        ## Verify nickname
        self.assertEqual(gc_obj.get_nickname(), 'Roundy')

        ## Verify email
        emails_work = gc_obj.get_email_work()
        self.assertTrue(len(emails_work) >= 1)
        self.assertEqual(emails_work[0], 'round@example.com')
        self.assertEqual(gc_obj.get_email_prim(), 'round@example.com')

        ## Verify phone
        phones_mob = gc_obj.get_phone_mob()
        self.assertTrue(len(phones_mob) >= 1)
        self.assertEqual(phones_mob[0][1] if isinstance(phones_mob[0], tuple) else phones_mob[0], '+1-555-0199')

        ## Verify org
        self.assertEqual(gc_obj.get_company(), 'TestCorp')
        self.assertEqual(gc_obj.get_title(), 'Engineer')
        self.assertEqual(gc_obj.get_dept(), 'R&D')

        ## Verify birthday
        self.assertEqual(gc_obj.get_birthday(), '1990-06-15')

        ## Verify website
        urls = gc_obj.get_web_home()
        self.assertTrue(len(urls) >= 1)
        self.assertEqual(urls[0], 'https://example.com')

    def test_e_gccontact_roundtrip (self):
        """Create a GCContact from properties, serialize to Person dict,
        and verify the mapping is correct."""
        from contact_gc import GCContact

        gc = GCContact(self.test_folder)
        self._populate_rich_contact(gc)

        person = gc.init_person_from_props()

        ## Now parse it back and verify round-trip
        gc2 = GCContact(self.test_folder, person=person)
        self._verify_rich_contact_fields(gc2)

        print('\n  Round-trip serialization: OK')

    def test_f_live_fidelity (self):
        """Create a GCContact with all fields, save it to the live Google API,
        read it back, and verify every field survived the round-trip."""
        from contact_gc import GCContact
        from folder_gc import PERSON_FIELDS

        gc = GCContact(self.test_folder)
        self._populate_rich_contact(gc)

        ## 1. Save to live Google API
        svc = self.pimdb.get_service()
        person_body = gc.init_person_from_props()

        ## Link to test folder
        person_body['memberships'] = [{
            'contactGroupMembership': {
                'contactGroupResourceName': self.test_gid
            }
        }]

        created = svc.people().createContact(
            body=person_body,
            personFields='names' # We don't need all fields on the response right now
        ).execute()

        rid = created.get('resourceName')
        self.assertIsNotNone(rid)

        ## 2. Read it back via live API
        fetched = svc.people().get(
            resourceName=rid,
            personFields=PERSON_FIELDS
        ).execute()

        ## 3. Parse it back into a GCContact and verify all fields are intact
        gc_fetched = GCContact(self.test_folder, person=fetched)
        self._verify_rich_contact_fields(gc_fetched)

        ## Clean up (optional since test_folder gets deleted, but good practice)
        svc.people().deleteContact(resourceName=rid).execute()

        print('\n  Live API field fidelity: OK')

def main ():
    global config, cs_file, gc_user

    best_effort = False

    # Parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], '',
                                   ['cs=', 'user=', 'best-effort'])
    except getopt.error as msg:
        print('Usage: python test_gc.py --cs /path/to/credentials.json '
              '[--user label] [--best-effort]')
        sys.exit(2)

    for option, arg in opts:
        if option == '--cs':
            cs_file = os.path.abspath(arg)
        elif option == '--user':
            gc_user = arg
        elif option == '--best-effort':
            best_effort = True

    # Validate the secrets file exists
    if cs_file and not os.path.exists(cs_file):
        print('ERROR: Client secrets file not found: %s' % cs_file)
        sys.exit(1)

    # Set up the environment
    setup_user_dir()       # wipes and recreates user_dir/
    setup_gc_creds_dir()   # creates gc_creds/ if it doesn't exist (persistent)

    # Copy the client secrets into gc_creds/ on first use
    if cs_file:
        dest = os.path.join(gc_creds_dir, os.path.basename(cs_file))
        if not os.path.exists(dest):
            shutil.copyfile(cs_file, dest)
        # Point cs_file to the copy inside gc_creds/
        cs_file = dest
    else:
        # No --cs provided; look for a cached client secrets .json in gc_creds/
        import glob
        jsons = [f for f in glob.glob(os.path.join(gc_creds_dir, '*.json'))
                 if os.path.basename(f) not in ('state.json', 'config.json')]
        if jsons:
            cs_file = jsons[0]
            logging.info('Using cached client secrets: %s', cs_file)
        elif best_effort:
            ## Invoked via 'make all' -- skip gracefully
            logging.warning('No cached credentials in %s/ -- GC tests will '
                            'be skipped.', gc_creds_dir)
            logging.warning('To enable GC tests (one-time setup):')
            logging.warning('  make gc GOOGLE_CL_SECRET=/path/to/client_secret.json')
            logging.warning('Get client_secret.json from Google Cloud Console '
                            '(APIs & Services > Credentials > OAuth 2.0 '
                            'Client ID > Desktop app).')
            logging.warning('Credentials are cached; subsequent runs just '
                            'need: make all')
        else:
            ## Invoked via 'make gc' explicitly -- hard error
            print('ERROR: No --cs provided and no cached credentials in %s/'
                  % gc_creds_dir)
            print('First run requires:')
            print('  make gc GOOGLE_CL_SECRET=/path/to/client_secret.json')
            sys.exit(1)

    config = Config(asynk_base_dir='../../', user_dir=gc_creds_dir)

    ## Discover all available Google test accounts for round-robin
    global _gc_accounts
    _gc_accounts = discover_gc_accounts(gc_creds_dir)
    if len(_gc_accounts) > 1:
        logging.info('Multi-account mode: %d accounts available (%s)',
                     len(_gc_accounts), ', '.join(_gc_accounts))
    elif _gc_accounts:
        logging.info('Single account mode: %s', _gc_accounts[0])

    # Remove our custom args from sys.argv so unittest doesn't choke
    sys.argv = [sys.argv[0]]

    # Run the tests
    unittest.main(verbosity=2)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()
