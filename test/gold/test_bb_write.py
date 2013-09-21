##
## Created : Sat Apr 07 20:03:04 IST 2012
##
## Copyright (C) 2012, 2013 Sriram Karra <karra.etc@gmail.com>
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
#####
##
## This unit test file is used to test BBDB file parsing and processing
## functionality in ASynK
##
## Usage is: python test_bb_write.py

import glob, logging, os, re, shutil, sys, traceback, unittest

## Being able to fix the sys.path thusly makes is easy to execute this
## script standalone from IDLE. Hack it is, but what the hell.
CUR_DIR     = os.path.abspath(os.path.dirname(__file__))
DIR_PATH    = os.path.abspath(os.path.join(CUR_DIR, "..", ".."))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk')]
sys.path = EXTRA_PATHS + sys.path

from state         import Config
from pimdb_bb      import BBPIMDB
from folder_bb     import BBContactsFolder
from contact_bb    import BBContact

asynk_base_dir = DIR_PATH
user_dir   = os.path.abspath('user_dir')
state_src  = os.path.join('..', '..', 'state.init.json')
state_dest = os.path.join(user_dir, 'state.json')

confnv6_src = os.path.join('..', '..', 'config', 'config_v6.json')
confn_dest  = os.path.join(user_dir, 'config.json')
conf_src = confnv6_src

def usage ():
    print 'Usage: python test_bb_write.py'

def main (argv=None):
    ## First setup the config files
    if os.path.exists(user_dir):
        logging.debug('Clearing user directory: %s', user_dir)
        shutil.rmtree(user_dir)
    else:
        logging.debug('Creating user directory: %s', user_dir)

    os.makedirs(user_dir)

    shutil.copyfile(state_src, state_dest)
    shutil.copyfile(conf_src, confn_dest)

    global config
    config = Config(asynk_base_dir=asynk_base_dir, user_dir=user_dir)

    ## Now run the write and read test cases
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBBDBWrite)
    unittest.TextTestRunner(verbosity=2).run(suite)

class TestBBDBWrite(unittest.TestCase):
    def setUp (self):
        self.config = config
        self.bbdbfn = os.path.join(CUR_DIR, "temp.bbdb")
        self.bb     = BBPIMDB(self.config, self.bbdbfn)
        ms   = self.bb.get_def_msgstore()
        self.deff = ms.get_folder(ms.get_def_folder_name())

    def tearDown (self):
        os.remove(self.bbdbfn)
        
    def parse (self, bbfn):
        ## Just open and parse the file. Any exceptions will be thrown up any way.
        bb = BBPIMDB(self.config, self.bbdbfn)

    def test_basic (self):
        con = BBContact(self.deff)
        con.set_name('Sri Venkata Sri Rama Subramanya Anjeneya Annapurna Sharma')
        con.set_prefix('Mr.')
        con.set_nickname('Karra')
        con.set_gender('Male')
        con.add_phone_mob(('Mobile', '+91 90084 88997'))
        con.add_notes('And so it goes...')

        self.deff.add_contact(con)
        self.deff.set_dirty()
        self.deff.save()
        self.parse(self.bbdbfn)

        # self.deff.print_contacts(name='Sri')

if __name__ == '__main__':
    if '--debug' in sys.argv:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.ERROR)

    main()