##
## Created : Fri Mar 11 12:11:54 PST 2022
##
## Copyright (C) 2022 Sriram Karra <karra.etc@gmail.com>
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
## This unit test file is used to test the Goolge Contacts connector is
## workingfine. This was created as part of the transition Contacts API V3 to
## the People API.
##
## Usage is: python test_gc_ready.py <google-account>
##

import glob, logging, os, re, shutil, sys, traceback, unittest

## Being able to fix the sys.path thusly makes is easy to execute this
## script standalone from IDLE. Hack it is, but what the hell.
DIR_PATH    = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath('__file__')), '../..'))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk')]
sys.path = EXTRA_PATHS + sys.path

from state         import Config
from pimdb_gc      import GCPIMDB
from folder_gc     import GCContactsFolder
from contact_gc    import GCContact
from gdata.client  import BadAuthentication

asynk_base_dir = os.path.abspath(os.path.join("..", ".."))
user_dir   = os.path.abspath('user_dir')
state_src  = os.path.join('..', '..', 'state.init.json')
state_dest = os.path.join(user_dir, 'state.json')

confnv6_src = os.path.join('..', '..', 'config', 'config_v6.json')
confn_dest  = os.path.join(user_dir, 'config.json')
conf_src = confnv6_src

def usage ():
    print 'Usage: python test_gc_ready.py <google-account>'

def main (argv=None):
    print 'Command line: ', sys.argv

    ## Initial set up of the config directories.

    if os.path.exists(user_dir):
        ## FIXME: We should probably find a way to retain oauth tokens and stuff;
        ## optionally restoring them
        logging.debug('Clearing user directory: %s', user_dir)
        # shutil.rmtree(user_dir)
    else:
        logging.debug('Creating user directory: %s', user_dir)
        os.makedirs(user_dir)

        shutil.copyfile(state_src, state_dest)
        shutil.copyfile(conf_src, confn_dest)

    global config
    config = Config(asynk_base_dir=asynk_base_dir, user_dir=user_dir)

    if len(sys.argv) > 1:
        print "Running tests for Google account: ", sys.argv[1]
        run(sys.argv[1])
    else:
        print "Error! ",
        usage()

def run (username):
    ## FIXME: This client secrets file is just a sym link to a karra.etc.json
    ## file. You may want to rename it to something you have access to.
    cs = os.path.join("./", "gc-test-client-secrets.json")
    cs = os.path.abspath(os.path.expanduser(cs))
    try:
        ## First some basic sanity tests

        # Test 1: just connect to Google and create a db and print out folders
        gc = GCPIMDB(config, username, cs)
        # gc.print_groups()

        # Test 2: List contacts in a folder; assumes this exists, of course
        gc.show_folder("contactGroups/4ed5a8dc8885aa3d")
    except BadAuthentication, e:
        raise AsynkCollectionError('Invalid Google credentials (%s)' % e)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()
