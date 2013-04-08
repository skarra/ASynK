##
## Created       : Sun Jun 17 18:01:02 IST 2012
## Last Modified : Sun Jun 17 18:43:03 IST 2012
##
## Copyright (C) 2012 Sriram Karra <karra.etc@gmail.com>
##
## This file is part of ASynK
##
## ASynK is free software: you can redistribute it and/or modify it under
## the terms of the GNU Affero General Public License as published by the
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
DIR_PATH    = os.path.abspath(os.path.dirname(os.path.realpath('../Gout')))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk')]
sys.path = EXTRA_PATHS + sys.path

conf_fn    = '../config.json'
state_src  = '../state.init.json'
state_dest = './state.test.json'

from   state      import Config
from   pimdb_ol   import OLPIMDB
from   folder     import Folder

def main (argv=None):
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOLTasksFunctions)
    unittest.TextTestRunner(verbosity=2).run(suite)

class TestOLTasksFunctions(unittest.TestCase):
    ## This module is for quick testing of the Config read/write
    ## functionality. We will make a quick copy of the main example config
    ## file into the current directory and start mucking with it.

    def setUp (self):
        shutil.copyfile(state_src, state_dest)
        self.config = Config(confn=conf_fn, staten=state_dest)
        self.ol     = OLPIMDB(self.config)
        self.deff   = self.ol.get_def_folder()

    def test_list_task_folders (self):
        fs = self.ol.get_folders(Folder.TASK_t)
        logging.debug('Number of task folders: %d', len(fs))
        for i, f in enumerate(fs):
            logging.debug('  Num %2d. Name: %s', i, f.get_name())
            f.print_key_stats()


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()  
