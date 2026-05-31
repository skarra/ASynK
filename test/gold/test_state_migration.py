##
## Created : Fri May 30 2026
## SPDX-FileCopyrightText: 2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
##
## Tests for state.json version migration framework.

import json, logging, os, os.path, shutil, sys, unittest

## Fix sys.path so we can import from asynk/
DIR_PATH    = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath('__file__')), '../..'))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk')]
sys.path = EXTRA_PATHS + sys.path

from state import Config, AsynkConfigError

ASYNK_BASE  = '../../'
USER_DIR    = os.path.abspath('user_dir_migration')
STATE_V5    = os.path.join('.', 'state.v5.test.json')
STATE_DEST  = os.path.join(USER_DIR, 'state.json')


def _setup_user_dir (state_src):
    """Create a fresh user directory and copy in the given state file."""
    if os.path.exists(USER_DIR):
        shutil.rmtree(USER_DIR)
    os.makedirs(USER_DIR)
    shutil.copyfile(state_src, STATE_DEST)


def _load_config (state_src=STATE_V5):
    """Set up user dir from state_src and return a Config instance."""
    _setup_user_dir(state_src)
    return Config(asynk_base_dir=ASYNK_BASE, user_dir=USER_DIR)


def _read_state_from_disk ():
    """Read and parse the on-disk state.json file."""
    with open(STATE_DEST, 'r') as f:
        return json.loads(f.read())


class TestStateMigrationV5toV6(unittest.TestCase):
    """Tests for the v5 -> v6 state.json migration."""

    @classmethod
    def setUpClass (cls):
        cls.config = _load_config(STATE_V5)

    @classmethod
    def tearDownClass (cls):
        if os.path.exists(USER_DIR):
            shutil.rmtree(USER_DIR)

    def test_v5_migrated_to_v6 (self):
        """After loading a v5 state, file_version should be 6."""
        self.assertEqual(self.config.get_state_file_version(), 6)

    def test_gc_username_backfilled (self):
        """GC collections should get username='default' backfilled."""
        for pname in ('gcbb', 'gcol', 'gcex'):
            coll_1 = self.config.get_coll_1(pname)
            self.assertEqual(coll_1.get('username'), 'default',
                             'username not backfilled in %s/coll_1' % pname)

    def test_gc_email_placeholder (self):
        """GC collections should get gc_email=None as placeholder."""
        for pname in ('gcbb', 'gcol', 'gcex'):
            coll_1 = self.config.get_coll_1(pname)
            self.assertIn('gc_email', coll_1,
                          'gc_email missing in %s/coll_1' % pname)
            self.assertIsNone(coll_1['gc_email'],
                              'gc_email should be None in %s/coll_1' % pname)

    def test_folder_name_placeholder (self):
        """All collections should get folder_name=None as placeholder."""
        for pname in ('gcbb', 'gcol', 'bbbb', 'gcex'):
            for getter, label in [(self.config.get_coll_1, 'coll_1'),
                                  (self.config.get_coll_2, 'coll_2')]:
                coll = getter(pname)
                self.assertIn('folder_name', coll,
                              'folder_name missing in %s/%s' % (pname, label))
                self.assertIsNone(coll['folder_name'],
                                  'folder_name should be None in %s/%s'
                                  % (pname, label))

    def test_non_gc_no_username (self):
        """Non-GC collections should NOT get a username field added."""
        ## coll_2 of gcbb is BB, coll_2 of gcol is OL, both colls of bbbb
        for pname, getter in [('gcbb', self.config.get_coll_2),
                              ('gcol', self.config.get_coll_2),
                              ('bbbb', self.config.get_coll_1),
                              ('bbbb', self.config.get_coll_2),
                              ('gcex', self.config.get_coll_2)]:
            coll = getter(pname)
            self.assertNotIn('username', coll,
                             'username should not be in non-GC coll: '
                             '%s/%s' % (pname, coll.get('dbid')))

    def test_non_gc_no_gc_email (self):
        """Non-GC collections should NOT get a gc_email field."""
        for pname, getter in [('gcbb', self.config.get_coll_2),
                              ('gcol', self.config.get_coll_2),
                              ('bbbb', self.config.get_coll_1),
                              ('bbbb', self.config.get_coll_2),
                              ('gcex', self.config.get_coll_2)]:
            coll = getter(pname)
            self.assertNotIn('gc_email', coll,
                             'gc_email should not be in non-GC coll: '
                             '%s/%s' % (pname, coll.get('dbid')))

    def test_existing_profile_fields_preserved (self):
        """Original profile fields (sync_dir, etc.) survive migration."""
        self.assertEqual(self.config.get_sync_dir('gcbb'), 'SYNC2WAY')
        self.assertEqual(self.config.get_sync_dir('gcol'), 'SYNC1WAY')
        self.assertEqual(self.config.get_conflict_resolve('gcbb'), 'gc')

    def test_state_file_written (self):
        """The on-disk state.json should reflect the migrated state."""
        disk = _read_state_from_disk()
        self.assertEqual(disk['file_version'], 6)
        self.assertEqual(disk['profiles']['gcbb']['coll_1']['username'],
                         'default')
        self.assertIsNone(disk['profiles']['gcbb']['coll_1']['gc_email'])
        self.assertIsNone(disk['profiles']['bbbb']['coll_1']['folder_name'])
        self.assertNotIn('username',
                         disk['profiles']['bbbb']['coll_1'])


class TestStateMigrationIdempotent(unittest.TestCase):
    """A v6 state should not be modified by the migration framework."""

    @classmethod
    def setUpClass (cls):
        """Load a v5 state (triggers migration to v6), save it, then
        reload and capture the result."""
        _setup_user_dir(STATE_V5)
        Config(asynk_base_dir=ASYNK_BASE, user_dir=USER_DIR)

        ## Read the migrated state from disk
        with open(STATE_DEST, 'r') as f:
            cls.state_after_first = f.read()

        ## Reload — this should NOT trigger another migration
        cls.config = Config(asynk_base_dir=ASYNK_BASE, user_dir=USER_DIR)

        with open(STATE_DEST, 'r') as f:
            cls.state_after_second = f.read()

    @classmethod
    def tearDownClass (cls):
        if os.path.exists(USER_DIR):
            shutil.rmtree(USER_DIR)

    def test_v6_not_remigrated (self):
        """Version should still be 6 after reload."""
        self.assertEqual(self.config.get_state_file_version(), 6)

    def test_file_unchanged_on_reload (self):
        """The on-disk state.json should be byte-identical after reload."""
        self.assertEqual(self.state_after_first, self.state_after_second)


class TestStateMigrationPreservesExisting(unittest.TestCase):
    """If a profile already has the new fields, migration must not
    overwrite them."""

    @classmethod
    def setUpClass (cls):
        """Create a v5 state with pre-existing new fields, run migration."""
        _setup_user_dir(STATE_V5)

        ## Patch the on-disk state to add pre-existing values
        with open(STATE_DEST, 'r') as f:
            state = json.loads(f.read())

        gcbb_c1 = state['profiles']['gcbb']['coll_1']
        gcbb_c1['username'] = 'myuser'
        gcbb_c1['gc_email'] = 'test@gmail.com'
        gcbb_c1['folder_name'] = 'My Contacts'

        with open(STATE_DEST, 'w') as f:
            f.write(json.dumps(state))

        cls.config = Config(asynk_base_dir=ASYNK_BASE, user_dir=USER_DIR)

    @classmethod
    def tearDownClass (cls):
        if os.path.exists(USER_DIR):
            shutil.rmtree(USER_DIR)

    def test_existing_username_preserved (self):
        coll = self.config.get_coll_1('gcbb')
        self.assertEqual(coll['username'], 'myuser')

    def test_existing_gc_email_preserved (self):
        coll = self.config.get_coll_1('gcbb')
        self.assertEqual(coll['gc_email'], 'test@gmail.com')

    def test_existing_folder_name_preserved (self):
        coll = self.config.get_coll_1('gcbb')
        self.assertEqual(coll['folder_name'], 'My Contacts')

    def test_version_still_bumped (self):
        """Even with pre-existing fields, version should be 6."""
        self.assertEqual(self.config.get_state_file_version(), 6)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main(verbosity=2)
