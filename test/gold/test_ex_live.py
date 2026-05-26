##
## Created : Sun May 25 22:00:00 PDT 2026
## SPDX-FileCopyrightText: 2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
## ####
##
## Integration tests for the Exchange Online (EX) connector using the
## Microsoft Graph API.  These tests require a real Azure AD / Entra ID
## app registration with Contacts.ReadWrite permissions.
##
## Prerequisites:
##   1. An Entra ID tenant with an app registration (see
##      doc/azure_app_registration.md)
##   2. The client_id configured in ASynK (config.py or config_v9.json)
##   3. Run with:
##        make ex-live EX_CLIENT_ID=YOUR-CLIENT-ID
##      or:
##        python test_ex_live.py --client-id YOUR-CLIENT-ID
##
##   On the first run you will be prompted to authenticate via device
##   code flow (browser-based).  Subsequent runs reuse the cached token
##   in ex_creds/.
##

import getopt, logging, os, os.path, shutil, sys, time, unittest

## Fix sys.path so we can import asynk modules
DIR_PATH    = os.path.dirname(os.path.dirname(os.path.dirname(
                  os.path.abspath(__file__))))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk')]
sys.path = EXTRA_PATHS + sys.path

from msgraph_client import (GraphAuthProvider, GraphContactsClient,
                             GraphAPIError)
from contact_ex    import EXContact, ASYNK_EXTENSION_NAME

## Directories
user_dir     = os.path.abspath('user_dir')
ex_creds_dir = os.path.abspath('ex_creds')   # persistent — survives 'make clean'
state_src    = os.path.join('.', 'state.test.json')
state_dest   = os.path.join(user_dir, 'state.json')

## These get filled in by main()
client    = None     # GraphContactsClient instance
client_id = None     # Azure AD app client ID
tenant_id = 'common' # Entra ID tenant

def setup_user_dir ():
    """Create (or re-create) a clean user_dir with state files."""
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)
    os.makedirs(user_dir)
    if os.path.exists(state_src):
        shutil.copyfile(state_src, state_dest)

def setup_ex_creds_dir ():
    """Ensure the persistent ex_creds/ directory exists.  Unlike user_dir/,
    this is NOT wiped on each run — it stores the MSAL token cache across
    test runs."""
    if not os.path.exists(ex_creds_dir):
        os.makedirs(ex_creds_dir)

def print_suite_banner (suite_name):
    print('\n' + '='*80)
    print('>>> INITIALIZING TEST SUITE: %s' % suite_name)
    print('='*80)

def print_test_banner (test_name):
    print('\n' + '-'*80)
    print('>> RUNNING TEST: %s' % test_name)
    print('-'*80)


## ---------------------------------------------------------------------------
## Test cases
## ---------------------------------------------------------------------------

class TestEXAuth(unittest.TestCase):
    """Test that we can authenticate and create a GraphContactsClient."""

    @classmethod
    def setUpClass (cls):
        print_suite_banner(cls.__name__)
        if client is None:
            raise unittest.SkipTest(
                'No Graph API client available; skipping EX tests.')

    def setUp (self):
        self.client = client
        print_test_banner(self._testMethodName)

    def test_client_exists (self):
        """After init, the GraphContactsClient should be available."""
        self.assertIsNotNone(self.client)

    def test_get_user_profile (self):
        """We should be able to read the authenticated user's profile."""
        profile = self.client._request('GET', '/me',
                                        params={'$select': 'displayName,mail'})
        self.assertIn('displayName', profile)
        print('  Authenticated as: %s (%s)' % (
            profile.get('displayName', '?'),
            profile.get('mail', profile.get('userPrincipalName', '?'))))


class TestEXFolders(unittest.TestCase):
    """Test contact folder operations via the Graph API."""

    @classmethod
    def setUpClass (cls):
        print_suite_banner(cls.__name__)
        if client is None:
            raise unittest.SkipTest(
                'No Graph API client available; skipping EX tests.')

    def setUp (self):
        self.client = client
        print_test_banner(self._testMethodName)

    def test_list_contact_folders (self):
        """list_contact_folders should return at least one folder (the
        default Contacts folder)."""
        folders = self.client.list_contact_folders()
        self.assertIsInstance(folders, list)
        self.assertGreater(len(folders), 0)

        print('\n  %-4s %-35s %s' % ('#', 'Name', 'Folder ID'))
        print('  ' + '-' * 75)
        for i, f in enumerate(folders, 1):
            print('  %-4d %-35s %s' % (
                i, f.get('displayName', ''), f.get('id', '')[:40] + '...'))

    def test_create_and_delete_folder (self):
        """Create a test folder, verify it exists, then delete it."""
        test_name = 'ASynK Test Folder (safe to delete)'

        ## Create
        result = self.client.create_contact_folder(test_name)
        self.assertIn('id', result)
        folder_id = result['id']
        self.assertEqual(result['displayName'], test_name)
        print('  Created folder: %s' % folder_id[:40])

        ## Verify it appears in the folder list
        folders = self.client.list_contact_folders()
        found = [f for f in folders if f['id'] == folder_id]
        self.assertEqual(len(found), 1)

        ## Delete
        self.client.delete_contact_folder(folder_id)
        print('  Deleted folder: %s' % folder_id[:40])

        ## Verify it's gone
        time.sleep(2)
        folders = self.client.list_contact_folders()
        found = [f for f in folders if f['id'] == folder_id]
        self.assertEqual(len(found), 0)


class TestEXContacts(unittest.TestCase):
    """Test contact CRUD operations via the Graph API.

    Tests b, c, d form a create -> update -> delete chain that shares
    a contact.  Tests a and e are independent."""

    TEST_FOLDER_NAME = 'ASynK Test Contacts (safe to delete)'

    @classmethod
    def setUpClass (cls):
        print_suite_banner(cls.__name__)
        if client is None:
            raise unittest.SkipTest(
                'No Graph API client available; skipping EX tests.')

        ## Create a dedicated test folder
        result = client.create_contact_folder(cls.TEST_FOLDER_NAME)
        cls._test_folder_id = result['id']
        cls._created_id = None
        logging.info('Created test folder: %s', cls._test_folder_id)

    @classmethod
    def tearDownClass (cls):
        """Clean up: delete the test folder (and all contacts in it)."""
        fid = getattr(cls, '_test_folder_id', None)
        if fid:
            try:
                client.delete_contact_folder(fid)
                logging.info('Deleted test folder: %s', fid)
            except Exception as e:
                logging.warning('Cleanup failed: %s', e)

    def setUp (self):
        self.client = client
        self.folder_id = self.__class__._test_folder_id
        print_test_banner(self._testMethodName)

    def test_a_list_contacts_empty (self):
        """Listing contacts in a freshly created folder should return
        an empty list."""
        contacts = self.client.list_contacts(folder_id=self.folder_id)
        self.assertIsInstance(contacts, list)
        self.assertEqual(len(contacts), 0)

    def test_b_create_and_read_contact (self):
        """Create a contact via the Graph API and read it back."""
        contact = {
            'givenName': 'TestFirst',
            'surname':   'TestLast',
            'emailAddresses': [
                {'address': 'test@example.com', 'name': 'Work Email'},
            ],
            'mobilePhone': '+1-555-0100',
        }

        result = self.client.create_contact(self.folder_id, contact)
        self.assertIn('id', result)
        cid = result['id']
        self.__class__._created_id = cid
        print('  Created contact: %s' % cid[:40])

        ## Read it back
        fetched = self.client.get_contact(cid)
        self.assertEqual(fetched['givenName'], 'TestFirst')
        self.assertEqual(fetched['surname'], 'TestLast')
        self.assertTrue(len(fetched.get('emailAddresses', [])) >= 1)
        self.assertEqual(fetched['emailAddresses'][0]['address'],
                         'test@example.com')

    def test_c_update_contact (self):
        """Update the previously created contact's name."""
        cid = self.__class__._created_id
        if not cid:
            self.skipTest('No contact created in previous test')

        patch_data = {'givenName': 'UpdatedFirst', 'surname': 'UpdatedLast'}
        result = self.client.update_contact(cid, patch_data)

        self.assertEqual(result['givenName'], 'UpdatedFirst')
        self.assertEqual(result['surname'], 'UpdatedLast')
        print('  Updated contact: %s' % cid[:40])

    def test_d_delete_contact (self):
        """Delete the previously created contact."""
        cid = self.__class__._created_id
        if not cid:
            self.skipTest('No contact created in previous test')

        self.client.delete_contact(cid)
        print('  Deleted contact: %s' % cid[:40])

        ## Verify it's gone
        time.sleep(1)
        try:
            self.client.get_contact(cid)
            self.fail('Contact should have been deleted')
        except GraphAPIError as e:
            self.assertIn(e.status_code, [404, 410])


class TestEXContactRoundTrip(unittest.TestCase):
    """Test EXContact field fidelity through the live Graph API.

    Creates a rich contact using EXContact, writes it to the Graph API,
    reads it back, and verifies all fields survived the round-trip."""

    TEST_FOLDER_NAME = 'ASynK Roundtrip Test (safe to delete)'

    @classmethod
    def setUpClass (cls):
        print_suite_banner(cls.__name__)
        if client is None:
            raise unittest.SkipTest(
                'No Graph API client available; skipping EX tests.')

        result = client.create_contact_folder(cls.TEST_FOLDER_NAME)
        cls._test_folder_id = result['id']

    @classmethod
    def tearDownClass (cls):
        fid = getattr(cls, '_test_folder_id', None)
        if fid:
            try:
                client.delete_contact_folder(fid)
            except Exception as e:
                logging.warning('Cleanup failed: %s', e)

    def setUp (self):
        self.client = client
        self.folder_id = self.__class__._test_folder_id
        print_test_banner(self._testMethodName)

    def _populate_rich_contact (self, exc):
        """Populate an EXContact with all supported field types."""
        exc.set_firstname('RoundFirst')
        exc.set_lastname('RoundLast')
        exc.set_middlename('M')
        exc.set_prefix('Dr')
        exc.set_suffix('Jr')
        exc.set_nickname('Roundy')
        exc.add_email_work('round.work@example.com')
        exc.add_email_home('round.home@example.com')
        exc.set_email_prim('round.work@example.com')
        exc.add_phone_mob(('Mobile', '+1-555-0199'))
        exc.add_phone_home(('Home', '+1-555-0101'))
        exc.add_phone_work(('Work', '+1-555-0102'))
        exc.set_company('TestCorp')
        exc.set_title('Engineer')
        exc.set_dept('R&D')
        exc.set_birthday('1990-06-15')
        exc.add_web_home('https://example.com')
        exc.add_web_work('https://work.example.com')
        exc.add_notes('A test contact for ASynK round-trip verification.')

    def _verify_rich_contact_fields (self, exc):
        """Verify all fields survived the round-trip."""
        ## Names
        self.assertEqual(exc.get_firstname(), 'RoundFirst')
        self.assertEqual(exc.get_lastname(), 'RoundLast')
        self.assertEqual(exc.get_middlename(), 'M')
        self.assertEqual(exc.get_prefix(), 'Dr')
        self.assertEqual(exc.get_suffix(), 'Jr')
        self.assertEqual(exc.get_nickname(), 'Roundy')

        ## Emails
        emails_work = exc.get_email_work()
        self.assertTrue(len(emails_work) >= 1)
        self.assertIn('round.work@example.com',
                       [e if isinstance(e, str) else e[0] for e in emails_work])

        emails_home = exc.get_email_home()
        self.assertTrue(len(emails_home) >= 1)
        self.assertIn('round.home@example.com',
                       [e if isinstance(e, str) else e[0] for e in emails_home])

        ## Phones
        phones_mob = exc.get_phone_mob()
        self.assertTrue(len(phones_mob) >= 1)

        ## Organization
        self.assertEqual(exc.get_company(), 'TestCorp')
        self.assertEqual(exc.get_title(), 'Engineer')
        self.assertEqual(exc.get_dept(), 'R&D')

        ## Birthday
        bday = exc.get_birthday()
        self.assertIsNotNone(bday)
        self.assertIn('1990', str(bday))

        ## Websites
        urls_home = exc.get_web_home()
        self.assertTrue(len(urls_home) >= 1)
        self.assertIn('https://example.com', urls_home)

        ## Notes
        notes = exc.get_notes()
        self.assertTrue(len(notes) >= 1)

    def test_a_excontact_local_roundtrip (self):
        """Create an EXContact, serialize to Graph dict, parse it back,
        and verify all fields survive (no network)."""
        exc = EXContact(folder=None)
        self._populate_rich_contact(exc)

        ## Serialize to Graph JSON dict
        graph_dict = exc.to_graph_dict()
        self.assertIn('givenName', graph_dict)
        self.assertEqual(graph_dict['givenName'], 'RoundFirst')

        ## Parse back from Graph JSON
        exc2 = EXContact(folder=None, graph_con=graph_dict)
        self._verify_rich_contact_fields(exc2)

        print('\n  Local round-trip serialization: OK')

    def test_b_live_field_fidelity (self):
        """Create an EXContact, write it to the live Graph API, read it
        back, and verify all fields survived."""
        exc = EXContact(folder=None)
        self._populate_rich_contact(exc)

        ## 1. Write to live Graph API
        graph_dict = exc.to_graph_dict()
        created = self.client.create_contact(self.folder_id, graph_dict)
        cid = created.get('id')
        self.assertIsNotNone(cid)
        print('  Created contact: %s' % cid[:40])

        ## Write extension data (phone labels, overflow)
        ext_data = exc.get_extension_data()
        if ext_data:
            self.client.set_extension(cid, ASYNK_EXTENSION_NAME, ext_data)
            print('  Wrote extension data')

        ## 2. Read back from live Graph API (with extensions)
        fetched = self.client.get_contact(cid, expand='extensions')
        self.assertIsNotNone(fetched)

        ## 3. Parse into EXContact and verify all fields
        exc_fetched = EXContact(folder=None, graph_con=fetched)
        self._verify_rich_contact_fields(exc_fetched)

        ## 4. Clean up
        self.client.delete_contact(cid)

        print('\n  Live API field fidelity: OK')

    def test_c_extension_persistence (self):
        """Verify that Open Extension data survives write-read cycle."""
        ## Create a minimal contact
        contact = {'givenName': 'ExtTest', 'surname': 'Persist'}
        created = self.client.create_contact(self.folder_id, contact)
        cid = created['id']

        ## Write extension
        ext_data = {
            'syncTags': {'profile1:bb': 'remote-bb-id-123'},
            'customData': {'gender': 'Male', 'anniversary': '2020-01-01'},
        }
        self.client.set_extension(cid, ASYNK_EXTENSION_NAME, ext_data)

        ## Read it back
        fetched_ext = self.client.get_extension(cid, ASYNK_EXTENSION_NAME)
        self.assertIsNotNone(fetched_ext)
        self.assertEqual(fetched_ext['syncTags']['profile1:bb'],
                         'remote-bb-id-123')
        self.assertEqual(fetched_ext['customData']['gender'], 'Male')

        ## Update extension
        ext_data['syncTags']['profile2:gc'] = 'remote-gc-id-456'
        self.client.set_extension(cid, ASYNK_EXTENSION_NAME, ext_data)

        ## Verify update
        fetched_ext2 = self.client.get_extension(cid, ASYNK_EXTENSION_NAME)
        self.assertEqual(fetched_ext2['syncTags']['profile2:gc'],
                         'remote-gc-id-456')

        ## Cleanup
        self.client.delete_contact(cid)

        print('\n  Extension persistence: OK')


class TestEXDeltaSync(unittest.TestCase):
    """Test delta (incremental) sync operations against the live API."""

    TEST_FOLDER_NAME = 'ASynK Delta Test (safe to delete)'

    @classmethod
    def setUpClass (cls):
        print_suite_banner(cls.__name__)
        if client is None:
            raise unittest.SkipTest(
                'No Graph API client available; skipping EX tests.')

        result = client.create_contact_folder(cls.TEST_FOLDER_NAME)
        cls._test_folder_id = result['id']

    @classmethod
    def tearDownClass (cls):
        fid = getattr(cls, '_test_folder_id', None)
        if fid:
            try:
                client.delete_contact_folder(fid)
            except Exception as e:
                logging.warning('Cleanup failed: %s', e)

    def setUp (self):
        self.client = client
        self.folder_id = self.__class__._test_folder_id
        print_test_banner(self._testMethodName)

    def test_delta_sync_lifecycle (self):
        """Full delta sync lifecycle:
        1. Initial sync (empty folder) → get delta link
        2. Add a contact
        3. Delta sync → should see the new contact
        4. Delete the contact
        5. Delta sync → should see the deletion
        """

        ## 1. Initial sync
        result1 = self.client.delta_sync(self.folder_id)
        self.assertEqual(len(result1.changed), 0)
        self.assertEqual(len(result1.deleted), 0)
        self.assertIsNotNone(result1.delta_link)
        print('  Initial delta link obtained')

        ## 2. Add a contact
        contact = {'givenName': 'DeltaTest', 'surname': 'Contact'}
        created = self.client.create_contact(self.folder_id, contact)
        cid = created['id']
        print('  Created contact: %s' % cid[:40])

        ## Small delay for server-side consistency
        time.sleep(2)

        ## 3. Delta sync — should see the new contact
        result2 = self.client.delta_sync(self.folder_id,
                                          delta_link=result1.delta_link)
        self.assertGreater(len(result2.changed), 0)
        changed_ids = [c['id'] for c in result2.changed]
        self.assertIn(cid, changed_ids)
        print('  Delta found %d changed, %d deleted' % (
            len(result2.changed), len(result2.deleted)))

        ## 4. Delete the contact
        self.client.delete_contact(cid)
        time.sleep(2)

        ## 5. Delta sync — should see the deletion
        result3 = self.client.delta_sync(self.folder_id,
                                          delta_link=result2.delta_link)
        self.assertGreater(len(result3.deleted), 0)
        self.assertIn(cid, result3.deleted)
        print('  Delta detected deletion: OK')


## ---------------------------------------------------------------------------
## main
## ---------------------------------------------------------------------------

def main ():
    global client, client_id, tenant_id

    best_effort = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], '',
                                   ['client-id=', 'tenant-id=', 'best-effort'])
    except getopt.error as msg:
        print('Usage: python test_ex_live.py --client-id YOUR-CLIENT-ID '
              '[--tenant-id TENANT] [--best-effort]')
        sys.exit(2)

    for option, arg in opts:
        if option == '--client-id':
            client_id = arg
        elif option == '--tenant-id':
            tenant_id = arg
        elif option == '--best-effort':
            best_effort = True

    ## Set up directories
    setup_user_dir()
    setup_ex_creds_dir()

    ## Determine client_id
    if not client_id:
        ## Try to read from a cached file in ex_creds/
        cid_file = os.path.join(ex_creds_dir, 'client_id')
        if os.path.exists(cid_file):
            with open(cid_file, 'r') as f:
                client_id = f.read().strip()
            logging.info('Using cached client_id from %s', cid_file)
        elif best_effort:
            logging.warning('No --client-id provided and no cached '
                            'credentials in %s/ -- EX live tests will '
                            'be skipped.', ex_creds_dir)
            logging.warning('To enable EX live tests (one-time setup):')
            logging.warning('  make ex-live EX_CLIENT_ID=YOUR-CLIENT-ID')
            logging.warning('See doc/azure_app_registration.md for setup.')
        else:
            print('ERROR: No --client-id provided and no cached client_id '
                  'in %s/' % ex_creds_dir)
            print('First run requires:')
            print('  make ex-live EX_CLIENT_ID=YOUR-CLIENT-ID')
            print('See doc/azure_app_registration.md for setup.')
            sys.exit(1)

    ## Cache the client_id for subsequent runs
    if client_id:
        cid_file = os.path.join(ex_creds_dir, 'client_id')
        with open(cid_file, 'w') as f:
            f.write(client_id)

        ## Authenticate via device code flow
        token_cache = os.path.join(ex_creds_dir, 'msal_token_cache.bin')
        try:
            auth = GraphAuthProvider(
                client_id=client_id,
                tenant_id=tenant_id,
                token_cache_path=token_cache)
            auth.authenticate()
            client = GraphContactsClient(auth)
            logging.info('Graph API client initialized successfully.')
        except Exception as e:
            if best_effort:
                logging.warning('Graph API auth failed: %s -- EX live tests '
                                'will be skipped.', e)
            else:
                print('ERROR: Graph API authentication failed: %s' % e)
                sys.exit(1)

    ## Remove our custom args from sys.argv so unittest doesn't choke
    sys.argv = [sys.argv[0]]

    ## Run the tests
    unittest.main(verbosity=2)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()
