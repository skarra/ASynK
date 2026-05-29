##
## Created : Sun Oct 05 18:59:40 IST 2014
## SPDX-FileCopyrightText: 2014-2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK

import logging, os, os.path, shutil, sys, traceback, unittest
from   subprocess import call

## Being able to fix the sys.path thusly makes is easy to execute this
## script standalone from IDLE. Hack it is, but what the hell.
DIR_PATH    = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '../..'))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk')]
sys.path = EXTRA_PATHS + sys.path

import utils
from   state          import Config

asynk_base_dir = os.path.abspath(os.path.join("..", ".."))
user_dir   = os.path.abspath('user_dir')
state_src  = os.path.join('..', '..', 'state.init.json')
state_dest = os.path.join(user_dir, 'state.json')

confn_src = os.path.join('..', '..', 'config',
                         Config.get_latest_config_filen(asynk_base_dir))
confn_dest  = os.path.join(user_dir, 'config.json')

def main (argv=None):
    if os.path.exists(user_dir):
        logging.debug('Clearing user directory: %s', user_dir)
        shutil.rmtree(user_dir)
    else:
        logging.debug('Creating user directory: %s', user_dir)

    os.makedirs(user_dir)

    shutil.copyfile(state_src, state_dest)
    shutil.copyfile(confn_src, confn_dest)

    # global config
    # config = Config(asynk_base_dir=asynk_base_dir, user_dir=user_dir)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestMethods)
    unittest.TextTestRunner(verbosity=2).run(suite)

class TestMethods(unittest.TestCase):

    ## This module is for quick testing of the Config read/write
    ## functionality. We will make a quick copy of the main example config
    ## file into the current directory and start mucking with it.

    def setUp (self):
        self.prog = '../../asynk.py'
        self.DEVNULL = open(os.devnull, 'wb')
        self.reset_user_dir()

    def tearDown (self):
        self.DEVNULL.close()
        # Clean up any created test databases in current directory
        for f in ['temp_create_store.bbdb', 'test_sync_bb1.bbdb.bak', 'test_sync_bb2.bbdb.bak']:
            if os.path.exists(f):
                os.remove(f)

    def reset_user_dir(self):
        if os.path.exists(user_dir):
            shutil.rmtree(user_dir)
        os.makedirs(user_dir)
        shutil.copyfile(state_src, state_dest)
        shutil.copyfile(confn_src, confn_dest)

    def run_cmd(self, args):
        cmd = [sys.executable, self.prog] + args + ['--user-dir=%s' % user_dir]
        return call(cmd, stdout=self.DEVNULL, stderr=self.DEVNULL)

    def test_no_args (self):
        ret = self.run_cmd([])
        self.assertEqual(ret, 0)

    def test_help (self):
        ret = self.run_cmd(['--help'])
        self.assertEqual(ret, 0)

    def test_version (self):
        ret = self.run_cmd(['--version'])
        self.assertEqual(ret, 0)

    def test_invalid_subcommand (self):
        """An invalid subcommand should fail."""
        ret = self.run_cmd(['invalid-command'])
        self.assertNotEqual(ret, 0)

    def test_invalid_db_choice (self):
        """Verify that an invalid db choice is rejected by argparse."""
        ret = self.run_cmd(['profile', 'create', '--db', 'bb', 'xx',
                            '--folder', 'f1', 'f2', '--name', 'pname'])
        self.assertNotEqual(ret, 0)

    def test_missing_db (self):
        """folders list with no db arg should fail."""
        ret = self.run_cmd(['folders', 'list'])
        self.assertNotEqual(ret, 0)

    def test_list_profile_names (self):
        ret = self.run_cmd(['profile', 'names'])
        self.assertEqual(ret, 0)

    def test_list_profiles (self):
        ret = self.run_cmd(['profile', 'list'])
        self.assertEqual(ret, 0)

    def test_create_profile_ok (self):
        ret = self.run_cmd(['profile', 'create', '--db', 'cd', 'bb',
                            '--folder', 'default', 'default',
                            '--store', 'https://server.org:8443/', 'test/bbdb.olbb',
                            '--name', 'pname'])
        self.assertEqual(ret, 0)

    def test_create_profile_missing_folder (self):
        ret = self.run_cmd(['profile', 'create', '--db', 'cd', 'bb',
                            '--store', 'https://server.org:8443/', 'test/bbdb.olbb',
                            '--name', 'pname'])
        ## argparse will reject this because --folder is required
        self.assertNotEqual(ret, 0)

    def test_create_profile_missing_name (self):
        ret = self.run_cmd(['profile', 'create', '--db', 'cd', 'bb',
                            '--folder', 'default', 'default',
                            '--store', 'https://server.org:8443/', 'test/bbdb.olbb'])
        ## argparse will reject this because --name is required
        self.assertNotEqual(ret, 0)

    def test_create_profile_invalid_name (self):
        ret = self.run_cmd(['profile', 'create', '--db', 'bb', 'bb',
                            '--store', 'test_sync_bb1.bbdb', 'test_sync_bb2.bbdb',
                            '--folder', 'default', 'default',
                            '--name', 'invalid pname'])
        self.assertEqual(ret, 1)

    def test_create_profile_duplicate (self):
        ret1 = self.run_cmd(['profile', 'create', '--db', 'bb', 'bb',
                             '--store', 'test_sync_bb1.bbdb', 'test_sync_bb2.bbdb',
                             '--folder', 'default', 'default',
                             '--name', 'mybbprofile'])
        self.assertEqual(ret1, 0)
        ret2 = self.run_cmd(['profile', 'create', '--db', 'bb', 'bb',
                             '--store', 'test_sync_bb1.bbdb', 'test_sync_bb2.bbdb',
                             '--folder', 'default', 'default',
                             '--name', 'mybbprofile'])
        self.assertEqual(ret2, 1)

    def test_find_profile_not_found (self):
        ret = self.run_cmd(['profile', 'find', '--db', 'bb', 'bb',
                            '--folder', 'f1', 'f2'])
        self.assertEqual(ret, 0)

    def test_find_profile_found (self):
        # Create it first
        self.run_cmd(['profile', 'create', '--db', 'bb', 'bb',
                      '--store', 'test_sync_bb1.bbdb', 'test_sync_bb2.bbdb',
                      '--folder', 'default', 'default',
                      '--name', 'mybbprofile'])
        ret = self.run_cmd(['profile', 'find', '--db', 'bb', 'bb',
                            '--store', 'test_sync_bb1.bbdb', 'test_sync_bb2.bbdb',
                            '--folder', 'default', 'default'])
        self.assertEqual(ret, 0)

    def test_show_profile_not_found (self):
        ret = self.run_cmd(['profile', 'show', '--name', 'nonexistent'])
        self.assertEqual(ret, 0)

    def test_show_profile_found (self):
        self.run_cmd(['profile', 'create', '--db', 'bb', 'bb',
                      '--store', 'test_sync_bb1.bbdb', 'test_sync_bb2.bbdb',
                      '--folder', 'default', 'default',
                      '--name', 'mybbprofile'])
        ret = self.run_cmd(['profile', 'show', '--name', 'mybbprofile'])
        self.assertEqual(ret, 0)

    def test_del_profile (self):
        self.run_cmd(['profile', 'create', '--db', 'bb', 'bb',
                      '--store', 'test_sync_bb1.bbdb', 'test_sync_bb2.bbdb',
                      '--folder', 'default', 'default',
                      '--name', 'mybbprofile'])
        ret = self.run_cmd(['profile', 'delete', '--name', 'mybbprofile'])
        self.assertEqual(ret, 0)

    def test_create_store (self):
        ret = self.run_cmd(['store', 'create', 'bb',
                            '--store', 'temp_create_store.bbdb'])
        self.assertEqual(ret, 0)

    def test_create_store_invalid_db (self):
        ret = self.run_cmd(['store', 'create', 'gc',
                            '--store', 'dummy'])
        self.assertEqual(ret, 1)

    def test_list_folders_bb (self):
        ret = self.run_cmd(['folders', 'list', 'bb',
                            '--store', 'test_sync_bb1.bbdb'])
        self.assertEqual(ret, 0)

    def test_create_folder_bb (self):
        ret = self.run_cmd(['folders', 'create', 'bb',
                            '--store', 'test_sync_bb1.bbdb',
                            '--name', 'new_folder'])
        self.assertEqual(ret, 0)

    def test_show_folder_bb (self):
        ret = self.run_cmd(['folders', 'show', 'bb',
                            '--store', 'test_sync_bb1.bbdb'])
        self.assertEqual(ret, 0)

    def test_del_folder_bb (self):
        ret = self.run_cmd(['folders', 'delete', 'bb',
                            '--store', 'test_sync_bb1.bbdb'])
        self.assertEqual(ret, 0)

    def test_sync_dry_run (self):
        self.run_cmd(['profile', 'create', '--db', 'bb', 'bb',
                      '--store', 'test_sync_bb1.bbdb', 'test_sync_bb2.bbdb',
                      '--folder', 'default', 'default',
                      '--name', 'mybbprofile'])
        ret = self.run_cmd(['sync', '--name', 'mybbprofile', '--dry-run'])
        self.assertEqual(ret, 0)

    def test_clear_sync_artifacts (self):
        ret = self.run_cmd(['clear-artifacts', 'bb',
                            '--store', 'test_sync_bb1.bbdb',
                            '--label-regex', '.*'])
        self.assertEqual(ret, 0)

    def test_ex_auth_args (self):
        ret = self.run_cmd(['profile', 'list', '--ex-user', 'user1',
                            '--ex-token-cache', 'path1',
                            '--ex-client-id', 'clientid1'])
        self.assertEqual(ret, 0)

    def test_ex_auth_args_too_many (self):
        ret = self.run_cmd(['profile', 'list', '--ex-user', 'user1', 'user2', 'user3'])
        self.assertEqual(ret, 0)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()
