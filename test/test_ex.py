##
## Created : Mon Mar 31 16:26:27 IST 2014
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
## This file is used for some poking around with the EWS code of ASynK -
## stuff like print a contact from a bbdb database, test new changes to pimdb
## or folder code, etc. Essentially some test routines that are not really
## unit tests. code often moves from here to the unittest directory (gold/)
## after a while
##

import logging, os, os.path, sys, traceback

CUR_DIR           = os.path.abspath('')
ASYNK_BASE_DIR    = os.path.abspath('..')
EXTRA_PATHS = [os.path.join(ASYNK_BASE_DIR, 'lib'),
               os.path.join(ASYNK_BASE_DIR, 'asynk'),]
sys.path = EXTRA_PATHS + sys.path

from state         import Config
from pimdb_ex      import EXPIMDB

def main ():
    ex = init()

def init ():
    with open('auth.pwd', 'r') as inf:
        user = inf.readline().strip()
        pw   = inf.readline().strip()
        url  = inf.readline().strip()

    conf = Config(asynk_base_dir=ASYNK_BASE_DIR, user_dir='./')
    ex = EXPIMDB(conf, user, pw, url)
    # ex.new_folder("ASynK Contacts 1")

    # ex.list_folders(recursive=False)
    # ex.del_folder('AAAcAHNrYXJyYUBhc3luay5vbm1pY3Jvc29mdC5jb20ALgAAAAAA6tvK38NMgEiPrdzycecYvAEACf/6iQHYvUyNzrlQXzUQNgAAEaHsAwAA')

    f = ex.get_def_folder()
    cons = f.find_items(['AQAcAHNrYXJyAGFAYXN5bmsub25taWNyb3NvZnQuY29tAEYAAAPq28rfw0yASI+t3PJx5xi8BwAJ//qJAdi9TI3OuVBfNRA2AAACAQ8AAAAJ//qJAdi9TI3OuVBfNRA2AAACEMsAAAA='])
    print 'Found %d contacts' % len(cons)
    for con in cons:
        print con

    return ex

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()
