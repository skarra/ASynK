##
## Created : Sun Oct 05 18:59:40 IST 2014
##
## Copyright (C) 2014 Sriram Karra <karra.etc@gmail.com>
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
from   subprocess import call

## Being able to fix the sys.path thusly makes is easy to execute this
## script standalone from IDLE. Hack it is, but what the hell.
DIR_PATH    = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath('__file__')), '../..'))
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
        # self.config = config
        self.prog = '../../asynk_cmdline.py'
        self.DEVNULL = open(os.devnull, 'wb')

    def test_no_args (self):
        ret = call([self.prog], stdout=self.DEVNULL, stderr=self.DEVNULL)
        self.assertEqual(ret, 0)

    def test_help (self):
        ret = call([self.prog, '--help'], stdout=self.DEVNULL, stderr=self.DEVNULL)
        self.assertEqual(ret, 0)

    def test_create_profile_ok (self):
        ret = call([self.prog, '--op=create-profile', '--db', 'cd', 'bb',
                   '--folder', 'default', 'default',
                   '--store', 'https://server.org:8443/', 'test/bbdb.olbb',
                   '--name', 'pname',
                   '--user-dir=%s' % user_dir],
                   stdout=self.DEVNULL, stderr=self.DEVNULL)
        self.assertEqual(ret, 0)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()  
