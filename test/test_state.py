
import logging, os, os.path, shutil, sys, traceback, unittest

## Being able to fix the sys.path thusly makes is easy to execute this
## script standalone from IDLE. Hack it is, but what the hell.
DIR_PATH    = os.path.abspath(os.path.dirname(os.path.realpath('../Gout')))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk')]
sys.path = EXTRA_PATHS + sys.path

from   state import Config, AsynkConfigError

conf_fn    = '../config.json'
state_src  = '../state.init.json'
state_dest = './state.test.json'

shutil.copyfile(state_src, state_dest)
config = Config(confn=conf_fn, staten=state_dest)

def main (argv=None):
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStateFunctions)
    unittest.TextTestRunner(verbosity=2).run(suite)

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
        self.assertTrue(val == 2)

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

        self.assertTrue(val['last_sync_start'] == "1980-01-01T00:00:00.00+00:00")
        self.assertTrue(val['last_sync_stop'] == "1980-01-01T00:00:00.00+00:00")
        self.assertTrue(val['sync_dir'] == 'SYNC2WAY')

    def test_read_ol_guid (self):
        val = self.config.get_ol_guid()
        self.assertTrue(val == '{a1271100-ac2e-11e0-bc8b-0025644a821c}')

    def test_read_ol_gid_base (self):
        val = self.config.get_ol_gid_base('gc')
        self.assertTrue(val == 0x9001)

    ##
    ## Now onto the state.json accessors
    ##

    def test_read_state_file_version (self):
        val = self.config.get_state_file_version()
        self.assertTrue(val == 2)

    def test_write_state_file_version (self):
        self.config.set_state_file_version(5)
        val = self.config.get_state_file_version()
        self.assertTrue(val == 5)

    def test_read_sync_start (self):
        val = self.config.get_last_sync_start('sample')
        self.assertTrue(val == "1980-01-01T00:00:00.00+00:00")

    def test_write_sync_start (self):
        t =  self.config.get_curr_time()
        self.config.set_last_sync_start('sample', t)
        val = self.config.get_last_sync_start('sample')
        self.assertTrue(val == t)
        
    def test_read_sync_stop (self):
        val = self.config.get_last_sync_stop('sample')
        self.assertTrue(val =="1980-01-01T00:00:00.00+00:00")

    def test_write_sync_stop (self):
        t =  self.config.get_curr_time()
        self.config.set_last_sync_stop('sample', t)
        val = self.config.get_last_sync_stop('sample')
        self.assertTrue(val == t)

    def test_invalid_profile_read (self):
        with self.assertRaises(AsynkConfigError):
            val = self.config.get_last_sync_start('goofy')

    def test_read_sync_dir (self):
        val = self.config.get_sync_dir('sample')
        self.assertTrue(val == "SYNC2WAY")

    def test_write_sync_dir (self):
        self.config.set_sync_dir('sample', 'SYNC1WAY')
        val = self.config.get_sync_dir('sample')
        self.assertTrue(val == "SYNC1WAY")

    def test_write_invalid_sync_dir (self):
        with self.assertRaises(AsynkConfigError):
            self.config.set_sync_dir('sample', 'GOOFY')

    def test_read_cr (self):
        val = self.config.get_conflict_resolve('sample')
        self.assertTrue(val == 'gc')

    def test_write_cr (self):
        self.config.set_conflict_resolve('sample', 'bb')
        val = self.config.get_conflict_resolve('sample')
        self.assertTrue(val == 'bb')

    def test_write_invalid_cr (self):
        with self.assertRaises(AsynkConfigError):
            self.config.set_conflict_resolve('sample', 'GUPPY')

    def test_get_gid_next_gc (self):
        val = self.config.get_ol_next_gid('gc')
        self.assertTrue(val == 0x9001)

    def test_get_gid_next_bb (self):
        val = self.config.get_ol_next_gid('bb')
        self.assertTrue(val == 0x8001)

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

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()  
