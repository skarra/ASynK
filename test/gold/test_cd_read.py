##
## Created : Wed Sep 17 08:45:41 IST 2014
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
#####
##
## This unit test file is used to test vCard file parsing and processing
## functionality in ASynK
##
## Usage is: python test_cd.py <VCF file>

import glob, logging, os, re, shutil, sys, traceback, unittest

## Being able to fix the sys.path thusly makes is easy to execute this
## script standalone from IDLE. Hack it is, but what the hell.
DIR_PATH    = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath('__file__')), '../..'))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk')]
sys.path = EXTRA_PATHS + sys.path

from   state          import Config
from   pimdb_cd       import CDPIMDB
from   contact_cd     import CDContact
import vobject

asynk_base_dir = os.path.abspath(os.path.join("..", ".."))
user_dir   = os.path.abspath('user_dir')
state_src  = os.path.join('..', '..', 'state.init.json')
state_dest = os.path.join(user_dir, 'state.json')

confn_src = os.path.join('..', '..', 'config',
                         Config.get_latest_config_filen(asynk_base_dir))
confn_dest  = os.path.join(user_dir, 'config.json')

def usage ():
    print 'Usage: python test_cd.py'

def main (argv=None):
    print 'Command line: ', sys.argv
    print confn_src

    if os.path.exists(user_dir):
        logging.debug('Clearing user directory: %s', user_dir)
        shutil.rmtree(user_dir)
    else:
        logging.debug('Creating user directory: %s', user_dir)

    os.makedirs(user_dir)

    shutil.copyfile(state_src, state_dest)
    shutil.copyfile(confn_src, confn_dest)

    global config
    config = Config(asynk_base_dir=asynk_base_dir, user_dir=user_dir)

    data = None
    with open(sys.argv[1], "r") as f:
        data = f.read()
        
    print
    print data
    vco = vobject.readOne(data)
    print vco
    print vco.prettyPrint()
    con = CDContact(None, vco=vobject.readOne(data), debug_vcf=True)
    print unicode(con)

    print "Display Name: ", con.get_disp_name()
    print "VCO: ", con.init_vco_from_props().serialize()


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    main()
