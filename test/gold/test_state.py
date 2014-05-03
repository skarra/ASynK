##
## Created : Sat May 12 10:44:13 IST 2011
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

import logging, os, os.path, shutil, sys, traceback, unittest

## Being able to fix the sys.path thusly makes is easy to execute this
## script standalone from IDLE. Hack it is, but what the hell.
DIR_PATH    = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath('__file__')), '../..'))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk')]
sys.path = EXTRA_PATHS + sys.path

from   state import Config, AsynkConfigError
import utils

user_dir   = os.path.abspath('user_dir')
state_src  = os.path.join('.', 'state.test.json')
state_dest = os.path.join(user_dir, 'state.json')

confnv4_src = os.path.join('..', '..', 'config', 'config_v4.json')
confnv5_src = os.path.join('..', '..', 'config', 'config_v5.json')
confn_dest  = os.path.join(user_dir, 'config.json')
confnv4_src_dirty = os.path.join('.', 'config_v4.dirty.json')

config = None

def run (conf_src):
    if os.path.exists(user_dir):
        logging.debug('Clearing user directory: %s', user_dir)
        shutil.rmtree(user_dir)
    else:
        logging.debug('Creating user directory: %s', user_dir)

    os.makedirs(user_dir)

    shutil.copyfile(state_src, state_dest)
    shutil.copyfile(conf_src, confn_dest)

    global config
    config = Config(asynk_base_dir='../../', user_dir=user_dir)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestStateFunctions)
    unittest.TextTestRunner(verbosity=2).run(suite)

def main ():
    run(conf_src=confnv4_src)

    print
    print '*** Testing with dirty config. Program should abort. ***'
    print
    run(conf_src=confnv4_src_dirty)

class TestStateFunctions(unittest.TestCase):

    ## This module is for quick testing of the Config read/write
    ## functionality. We will make a quick copy of the main example config
    ## file into the current directory and start mucking with it.

    def setUp (self):
        self.config = config

    ##
    ## First the tests for accessors for data in config.json - all of these
    ## are essentially read tests.
    ##

    def test_get_conf_file_version (self):
        val = self.config.get_conf_file_version()
        self.assertEqual(val, 7)

    def test_read_label_prefix (self):
        val = self.config.get_label_prefix()
        self.assertTrue(val == 'asynk')

    def test_read_label_separator (self):
        val = self.config.get_label_separator()
        self.assertTrue(val == ':')

    ## Hard to compare entire dictionaries, so will stick to comparing a
    ## random field inside the ditionary. The rest should be alright.
    def test_read_db_config_ol (self):
        val = self.config.get_db_config('ol')
        self.assertTrue(val['sync_fields'][0] == 'PR_ENTRYID')

    def test_read_db_config_bb (self):
        val = self.config.get_db_config('bb')
        self.assertTrue(val['notes_map']['fileas'] == 'fileas')

    def test_read_profile_defaults (self):
        val = self.config.get_profile_defaults()

        self.assertTrue(val['coll_1']['dbid'] == None)
        self.assertTrue(val['coll_1']['stid'] == None)
        self.assertTrue(val['coll_1']['foid'] == None)

        self.assertTrue(val['coll_2']['dbid'] == None)
        self.assertTrue(val['coll_2']['stid'] == None)
        self.assertTrue(val['coll_2']['foid'] == None)

        self.assertTrue(val['last_sync_start'] == utils.time_start)
        self.assertTrue(val['last_sync_stop'] == utils.time_start)
        self.assertTrue(val['sync_dir'] == 'SYNC2WAY')

    def test_read_ol_guid (self):
        val = self.config.get_ol_guid()
        self.assertTrue(val == '{a1271100-ac2e-11e0-bc8b-0025644a821c}')

    def test_read_ol_gid_base (self):
        val = self.config.get_ol_gid_base('gc')
        self.assertTrue(val == 0x9001)

    def test_read_ol_cus_pid (self):
        val = self.config.get_ol_cus_pid()
        self.assertTrue(val == 0x6501)

    def test_read_ex_guid (self):
        val = self.config.get_ex_guid()
        self.assertTrue(val == 'c950b7d3-ca13-43cd-9e78-be65bbdeaf37')

    def test_read_ex_cus_pid (self):
        val = self.config.get_ex_cus_pid()
        self.assertTrue(val == 0x6501)

    def test_read_ex_stags_pname (self):
        val = self.config.get_ex_stags_pname()
        self.assertTrue(val == 'sync_tags')

    def test_read_backup_hold_period (self):
        val = self.config.get_backup_hold_period()
        self.assertEqual(val, 10)

    ##
    ## Now onto the state.json accessors
    ##

    def test_read_state_file_version (self):
        val = self.config.get_state_file_version()
        self.assertTrue(val == 4)

    def test_write_state_file_version (self):
        self.config.set_state_file_version(5)
        val = self.config.get_state_file_version()
        self.assertTrue(val == 5)

    def test_read_profile_names_cnt (self):
        ps = self.config.get_profile_names()
        self.assertEqual(len(ps), 3)

    def test_read_profile_names_vals (self):
        ps = self.config.get_profile_names()
        self.assertEqual(True, 'defgcol' in ps and 'defgcbb' in ps)

    def test_read_sync_start (self):
        val = self.config.get_last_sync_start('defgcol')
        self.assertTrue(val == utils.time_start)

    def test_write_sync_start (self):
        t =  self.config.get_curr_time()
        self.config.set_last_sync_start('defgcol', t)
        val = self.config.get_last_sync_start('defgcol')
        self.assertTrue(val == t)
        
    def test_read_sync_stop (self):
        val = self.config.get_last_sync_stop('defgcol')
        self.assertTrue(val == utils.time_start)

    def test_write_sync_stop (self):
        t =  self.config.get_curr_time()
        self.config.set_last_sync_stop('defgcol', t)
        val = self.config.get_last_sync_stop('defgcol')
        self.assertTrue(val == t)

    def test_invalid_profile_read (self):
        with self.assertRaises(AsynkConfigError):
            val = self.config.get_last_sync_start('goofy')

    def test_read_sync_dir (self):
        val = self.config.get_sync_dir('defgcol')
        self.assertTrue(val == "SYNC2WAY")

    def test_write_sync_dir (self):
        self.config.set_sync_dir('defgcol', 'SYNC1WAY')
        val = self.config.get_sync_dir('defgcol')
        self.assertTrue(val == "SYNC1WAY")

    def test_write_invalid_sync_dir (self):
        with self.assertRaises(AsynkConfigError):
            self.config.set_sync_dir('defgcol', 'GOOFY')

    def test_read_cr (self):
        val = self.config.get_conflict_resolve('defgcol')
        self.assertTrue(val == 'gc')

    def test_write_cr (self):
        self.config.set_conflict_resolve('defgcbb', 'bb')
        val = self.config.get_conflict_resolve('defgcbb')
        self.assertTrue(val == 'bb')

    def test_write_invalid_cr (self):
        with self.assertRaises(AsynkConfigError):
            self.config.set_conflict_resolve('defgcbb', 'GUPPY')

    def test_get_ol_gid_next_gc (self):
        val = self.config.get_ol_next_gid('gc')
        self.assertTrue(val == 0x9002)

    def test_get_ol_gid_next_bb (self):
        val = self.config.get_ol_next_gid('bb')
        self.assertTrue(val == 0x8001)

    def test_get_ol_gid_next_cd (self):
        val = self.config.get_ol_next_gid('cd')
        self.assertTrue(val == 0xa001)

    def test_get_ol_gid_next_ex (self):
        val = self.config.get_ol_next_gid('ex')
        self.assertTrue(val == 0xb001)

    def test_make_sync_label (self):
        val = self.config.make_sync_label('goofy', 'gc')
        self.assertTrue(val == 'asynk:goofy:gc')

        val = self.config.make_sync_label('goofy', 'gcol')
        self.assertTrue(val == 'asynk:goofy:gcol')    

    def test_parse_sync_label (self):
        val = 'asynk:goofy:gc'
        p, i = self.config.parse_sync_label(val)
        self.assertEqual(p, 'goofy')
        self.assertEqual(i, 'gc')

        val = 'asynk:goofy0123:gc'
        p, i = self.config.parse_sync_label(val)
        self.assertEqual(p, 'goofy0123')
        self.assertEqual(i, 'gc')

    def test_matching_pname_1 (self):
        ps = self.config.find_matching_pname('gc', None, None,
                                             'ol', None, None)
        self.assertEqual(True, not not ps)
        self.assertEqual(True, len(ps) == 1)
        self.assertEqual(True, ps[0] == 'defgcol')

    def test_matching_pname_2 (self):
        ps = self.config.find_matching_pname('gc', None, None,
                                             'bb', "~/.bbdb", "default")
        self.assertEqual(True, not not ps)
        self.assertEqual(True, len(ps) == 1)
        self.assertEqual(True, ps[0] == 'defgcbb')

    def test_matching_pname_3 (self):
        ps = self.config.find_matching_pname('gc', None, None,
                                             'bb', "~/.bbdb", None)
        self.assertEqual(True, not not ps)
        self.assertEqual(True, len(ps) == 1)
        self.assertEqual(True, ps[0] == 'defgcbb')

    def test_matching_pname_4 (self):
        ps = self.config.find_matching_pname('gc', None, None,
                                             'bb', None, "default")
        self.assertEqual(True, not not ps)
        self.assertEqual(True, len(ps) == 1)
        self.assertEqual(True, ps[0] == 'defgcbb')

    def test_matching_pname_5 (self):
        ps = self.config.find_matching_pname('gc', None, None,
                                             'bb', None, None)
        self.assertEqual(True, not not ps)
        self.assertEqual(True, len(ps) == 1)
        self.assertEqual(True, ps[0] == 'defgcbb')

    def test_get_store_pnames_1 (self):
        ps = self.config.get_store_pnames('gc')
        self.assertEqual(True, not not ps)
        self.assertEqual(True, len(ps) == 3)
        self.assertEqual(True, 'defgcol' in ps and 'defgcbb' in ps)

    def test_get_store_pnames_2 (self):
        ps = self.config.get_store_pnames('bb')
        self.assertEqual(False, not not ps)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()  
