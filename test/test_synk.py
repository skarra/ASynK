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

import argparse, logging, os, os.path, shutil, sys, traceback, unittest

## Being able to fix the sys.path thusly makes is easy to execute this
## script standalone from IDLE. Hack it is, but what the hell.
DIR_PATH    = os.path.abspath(os.path.dirname(os.path.realpath('../Gout')))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk'),
               DIR_PATH]
sys.path = EXTRA_PATHS + sys.path

from   state import Config, AsynkConfigError
from   asynk import Asynk, AsynkParserError
from   contact_gc import GCContact

conf_fn    = '../config.json'
state_src  = '../state.init.json'
state_dest = './state.test.json'

shutil.copyfile(state_src, state_dest)
config = Config(confn=conf_fn, staten=state_dest)

def main (argv=None):
    init()
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGCBBSyncFunctions)
    unittest.TextTestRunner(verbosity=2).run(suite)

def blank_uinps ():
    u = argparse.Namespace()
    u.db               = None
    u.op               = 'startweb'
    u.bbdb_file        = None
    u.dry_run          = False
    u.remote_db        = None
    u.profile_name     = None
    u.store_id         = None
    u.folder_name      = None
    u.folder_id        = None
    u.direction        = '2way'
    u.log              = 'info'
    u.label_regex      = None
    u.conflict_resolve = None
    u.item_id          = None
    u.user             = None
    u.pwd              = None
    u.port             = None

    return u

def init ():
    # Create a new folder on Google and set up a profile for working with
    # the stuff

    u = blank_uinps()
    u.db          = ['gc']
    u.folder_name = 'asynkunittest'
    u.log         = 'debug'
    u.op          = 'create_folder'

    # Create the Test Folder on Google
    asyn  = Asynk(u, config=config)
    gcfid = asyn.dispatch()
    gcdb  = asyn.get_db('gc')
    gcu   = asyn.get_gcuser()
    gcp   = asyn.get_gcpw()

    u.db          = ['bb']
    u.folder_name = 'test.bbdb'

    # Create the Test BBDB file
    asyn  = Asynk(u, config=config)
    bbfid = asyn.dispatch()
    bbdb  = asyn.get_db('bb')

    # Create a test profile between these two IDs
    u = blank_uinps()
    u.db           = ['gc', 'bb']
    u.folder_id    = [gcfid, bbfid]
    u.log          = 'debug'
    u.profile_name = 'asynunittest'
    u.op           = 'create_profile'

    u.gcfid = gcfid
    u.bbfid = bbfid

    asyn  = Asynk(u, config=config)
    asyn.dispatch()

    asyn.set_db('gc', gcdb)
    asyn.set_db('bb', bbdb)
    asyn.set_gcuser(gcu)
    asyn.set_gcpw(gcp)

    asynk(asyn)
    uinps(u)

def asynk (val='goofy'):
    global _asynk

    if val == 'goofy':
        return _asynk
    else:
        _asynk = val
        return val

def uinps (val=False):
    global _uinps

    if val:
        _uinps = val
        return val
    else:
        return _uinps

def create_gc_contact (asynk, uinps):
    gc     = asynk.get_db('gc')
    gcfid  = uinps.gcfid
    gcf, t = gc.find_folder(gcfid)

    con = GCContact(gcf)
    con.set_name('Sri Venkata Sri Rama Subramanya Anjeneya Annapurna Sharma')
    con.set_prefix('Mr.')
    con.set_nickname('Karra')
    #    con.set_gender('Male')
    con.add_phone_mob(('Mobile', '+91 90084 88997'))
    con.add_notes('And so it goes...')

    # FIXME: We should do a more exhaustive sort of contact, with multiple
    # entries of each type of possible entry and so on...

    return con.save()

class TestGCBBSyncFunctions(unittest.TestCase):
    def setUp (self):
        pass

    def test_new_gc_to_bb (self):
        """Sync a brand new contact from Google to BBDB"""

        a = asynk()
        u = uinps()
        conid = create_gc_contact(a, u)

        a.set_op('op_sync')
        a.dispatch()

        self.assertTrue(True)
        
if __name__ == "__main__":
    main()
