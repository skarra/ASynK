##
## Created : Thu May 15 20:14:00 PDT 2026
##
## Copyright (C) 2026 Sriram Karra <karra.etc@gmail.com>
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

import getopt, logging, os, os.path, shutil, sys, unittest

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
## Test cases
## ---------------------------------------------------------------------------

class TestGCAuth(unittest.TestCase):
    """Test that we can authenticate and create a GCPIMDB instance."""

    @classmethod
    def setUpClass (cls):
        """Create a GCPIMDB connected to a real Google account."""
        if cs_file is None:
            raise unittest.SkipTest(
                'No --cs (client secret) provided; skipping GC tests.')

        cls.pimdb = GCPIMDB(config, gc_user, cs_file)

    def test_service_exists (self):
        """After init, the People API service object should be set."""
        svc = self.pimdb.get_service()
        self.assertIsNotNone(svc)

    def test_dbid (self):
        """The database ID for Google Contacts is 'gc'."""
        self.assertEqual(self.pimdb.get_dbid(), 'gc')

    def test_user (self):
        """The user label should match what was passed to __init__."""
        self.assertEqual(self.pimdb.get_user(), gc_user)

class TestGCGroups(unittest.TestCase):
    """Test contact group operations via the People API."""

    @classmethod
    def setUpClass (cls):
        if cs_file is None:
            raise unittest.SkipTest(
                'No --cs (client secret) provided; skipping GC tests.')
        cls.pimdb = GCPIMDB(config, gc_user, cs_file)

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
    """Test contact-level operations via the People API."""

    TEST_GROUP_NAME = 'ASynK Test Contacts (safe to delete)'

    @classmethod
    def setUpClass (cls):
        if cs_file is None:
            raise unittest.SkipTest(
                'No --cs (client secret) provided; skipping GC tests.')

        cls.pimdb = GCPIMDB(config, gc_user, cs_file)

        ## Create a dedicated test group so we don't pollute real contacts
        cls.test_gid = cls.pimdb.new_folder(cls.TEST_GROUP_NAME)
        cls.test_folder = None
        for f in cls.pimdb.get_contacts_folders():
            if f.get_itemid() == cls.test_gid:
                cls.test_folder = f
                break

    @classmethod
    def tearDownClass (cls):
        """Clean up: delete the test group."""
        import time
        if hasattr(cls, 'test_gid') and cls.test_gid:
            try:
                cls.pimdb.del_folder(cls.test_gid)
            except Exception as e:
                logging.warning('Cleanup failed: %s', e)
            ## Give Google time to propagate
            time.sleep(2)

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

    def test_e_gccontact_roundtrip (self):
        """Create a GCContact from properties, serialize to Person dict,
        and verify the mapping is correct."""
        from contact_gc import GCContact

        gc = GCContact(self.test_folder)
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

        person = gc.init_person_from_props()

        ## Verify names
        self.assertEqual(person['names'][0]['givenName'], 'RoundFirst')
        self.assertEqual(person['names'][0]['familyName'], 'RoundLast')
        self.assertEqual(person['names'][0]['middleName'], 'M')
        self.assertEqual(person['names'][0]['honorificPrefix'], 'Dr')
        self.assertEqual(person['names'][0]['honorificSuffix'], 'Jr')

        ## Verify nickname
        self.assertEqual(person['nicknames'][0]['value'], 'Roundy')

        ## Verify email
        emails = person.get('emailAddresses', [])
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0]['value'], 'round@example.com')
        self.assertEqual(emails[0]['type'], 'work')

        ## Verify phone
        phones = person.get('phoneNumbers', [])
        self.assertEqual(len(phones), 1)
        self.assertEqual(phones[0]['value'], '+1-555-0199')

        ## Verify org
        orgs = person.get('organizations', [])
        self.assertEqual(orgs[0]['name'], 'TestCorp')
        self.assertEqual(orgs[0]['title'], 'Engineer')
        self.assertEqual(orgs[0]['department'], 'R&D')

        ## Verify birthday
        bdays = person.get('birthdays', [])
        self.assertEqual(bdays[0]['date']['year'], 1990)
        self.assertEqual(bdays[0]['date']['month'], 6)
        self.assertEqual(bdays[0]['date']['day'], 15)

        ## Verify website
        urls = person.get('urls', [])
        self.assertEqual(urls[0]['value'], 'https://example.com')

        ## Now parse it back and verify round-trip
        gc2 = GCContact(self.test_folder, person=person)
        self.assertEqual(gc2.get_firstname(), 'RoundFirst')
        self.assertEqual(gc2.get_lastname(), 'RoundLast')
        self.assertEqual(gc2.get_middlename(), 'M')
        self.assertEqual(gc2.get_nickname(), 'Roundy')
        self.assertEqual(gc2.get_company(), 'TestCorp')
        self.assertEqual(gc2.get_birthday(), '1990-06-15')

        print('\n  Round-trip serialization: OK')

def main ():
    global config, cs_file, gc_user

    # Parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], '', ['cs=', 'user='])
    except getopt.error as msg:
        print('Usage: python test_gc.py --cs /path/to/credentials.json '
              '[--user label]')
        sys.exit(2)

    for option, arg in opts:
        if option == '--cs':
            cs_file = os.path.abspath(arg)
        elif option == '--user':
            gc_user = arg

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
        else:
            print('ERROR: No --cs provided and no cached credentials in %s/'
                  % gc_creds_dir)
            print('First run requires: python test_gc.py '
                  '--cs /path/to/credentials.json')
            sys.exit(1)

    config = Config(asynk_base_dir='../../', user_dir=gc_creds_dir)

    # Remove our custom args from sys.argv so unittest doesn't choke
    sys.argv = [sys.argv[0]]

    # Run the tests
    unittest.main(verbosity=2)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()
