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
from pimdb_gc import GCPIMDB

## Directories
user_dir   = os.path.abspath('user_dir')
state_src  = os.path.join('.', 'state.test.json')
state_dest = os.path.join(user_dir, 'state.json')
confn_src  = os.path.join('..', '..', 'config', 'config_v4.json')
confn_dest = os.path.join(user_dir, 'config.json')

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

        # Verify it's gone
        found = self.pimdb.find_group(test_name)
        self.assertIsNone(found)

## ---------------------------------------------------------------------------
## Main — parse CLI args and run
## ---------------------------------------------------------------------------

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

    if cs_file and not os.path.exists(cs_file):
        print('ERROR: Client secrets file not found: %s' % cs_file)
        sys.exit(1)

    # Set up the environment
    setup_user_dir()
    config = Config(asynk_base_dir='../../', user_dir=user_dir)

    # Remove our custom args from sys.argv so unittest doesn't choke
    sys.argv = [sys.argv[0]]

    # Run the tests
    unittest.main(verbosity=2)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()
