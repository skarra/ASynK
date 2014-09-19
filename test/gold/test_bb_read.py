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
## Usage is: python test_bb.py <bbdbfile>

import glob, logging, os, re, shutil, sys, traceback, unittest

## Being able to fix the sys.path thusly makes is easy to execute this
## script standalone from IDLE. Hack it is, but what the hell.
DIR_PATH    = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath('__file__')), '../..'))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk')]
sys.path = EXTRA_PATHS + sys.path

from state         import Config
from pimdb_bb      import BBPIMDB
from folder_bb     import BBContactsFolder
from contact_bb    import BBContact

asynk_base_dir = os.path.abspath(os.path.join("..", ".."))
user_dir   = os.path.abspath('user_dir')
state_src  = os.path.join('..', '..', 'state.init.json')
state_dest = os.path.join(user_dir, 'state.json')

confnv4_src = os.path.join('..', '..', 'config', 'config_v4.json')
confnv5_src = os.path.join('..', '..', 'config', 'config_v5.json')
confnv6_src = os.path.join('..', '..', 'config', 'config_v6.json')
confn_dest  = os.path.join(user_dir, 'config.json')
confnv4_src_dirty = os.path.join('.', 'config_v4.dirty.json')
conf_src = confnv6_src

def usage ():
    print 'Usage: python test_bb.py'

def main (argv=None):
    print 'Command line: ', sys.argv

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

    if len(sys.argv) > 1:
        run(sys.argv[1])
    else:
        print "Running tests against all BBDB files in data/bb/..."
        bb_data_dir = os.path.join(asynk_base_dir, "test", "gold", "data",
                                   "bb")
        patt =  os.path.join(bb_data_dir, "*")
        test_inputs = glob.glob(patt)
        test_inputs.append(os.path.abspath('data/bb/bbdb.Non-Existent'))

        for f in test_inputs:
            print "Testing against input file: ", f
            run(f)

def run (fn):
    global bbfn
    bbfn = fn

    suite = unittest.TestLoader().loadTestsFromTestCase(TestBBDB)
    unittest.TextTestRunner(verbosity=2).run(suite)

class TestBBDB(unittest.TestCase):
    def setUp (self):
        self.config = config
        self.bbdbfn = bbfn
        self.bb = BBPIMDB(self.config, bbfn)

    def test_parse (self):
        self.bb = BBPIMDB(self.config, bbfn)

    def test_ver (self):
        ver_check = self.get_ver_from_filename()
        # print "Ver_check: ", ver_check
        if ver_check:
            assert(ver_check == self.bb.get_def_msgstore().get_file_format())

    def get_ver_from_filename (self):
        v = re.search('\.v(\d+)\.', self.bbdbfn)
        return v.group(1) if v else None

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    main()

## FIXME: Sat Aug 10 10:26:52 IST 2013 There needs to be an entry point to
## this stuff - which is essentially a way to explore the BBDB contents
## through the eyes of ASynK.

# def rest ():
#     tests = TestBBContact(config_fn='../config.json',
#                           state_fn='./state.json',
#                           bbfn=bbfn)
#     if len(sys.argv) > 2:
#         name = sys.argv[2]
#     else:
#         name = 'Amma'

#     tests.print_contacts(name=name)
#     # tests.write_to_file()

# class TestBBContact:
#     def __init__ (self, config_fn, state_fn, bbfn):
#         logging.debug('Getting started... Reading Config File...')

#         self.config = Config(config_fn, state_fn)
#         self.bb     = BBPIMDB(self.config, bbfn)
#         ms          = self.bb.get_def_msgstore()
#         self.deff   = ms.get_folder(ms.get_def_folder_name())

#     def print_contacts (self, cnt=0, name=None):
#         self.deff.print_contacts(cnt=cnt, name=name)

#     def write_to_file (self):
#         self.deff.save()
