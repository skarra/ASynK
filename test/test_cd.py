##
## Created : Tue Apr 02 13:32:55 IST 2013
##
## Copyright (C) 2013 Sriram Karra <karra.etc@gmail.com>
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
## This file is used for some poking around with the BBDB code of ASynK -
## stuff like print a contact from a bbdb database, test new changes to pimdb
## or folder code, etc. Essentially some test routines that are not really
## unit tests. code often moves from here to the unittest directory (gold/)
## after a while

import logging, os, sys

## Being able to fix the sys.path thusly makes is easy to execute this
## script standalone from IDLE. Hack it is, but what the hell.
CUR_DIR           = os.path.abspath('')
ASYNK_BASE_DIR    = os.path.abspath('..')
EXTRA_PATHS       = [os.path.join(ASYNK_BASE_DIR, 'lib'),
                     os.path.join(ASYNK_BASE_DIR, 'asynk'),]
sys.path          = EXTRA_PATHS + sys.path

from state         import Config
from pimdb_cd      import CDPIMDB
from contact_cd    import CDContact

def new_folder (cd, name=None):
    cd.new_folder(fname=name if name else 'goofy')

def main (argv=None):
    conf = Config(os.path.join('..', 'config.json'), 'state.test.json')
    user = raw_input('Enter Username:')
    pw   = raw_input('Password:')
    cd   = CDPIMDB(conf, 'https://localhost:8443', user, pw)

    root = '/addressbooks/__uids__/skarrag/addressbook/'

    # create_contact(cd)
    show_def_folder(cd, True)
    # multi_get(cd, root)
    # get(cd, root)

def get (cd, root):
    fi = cd.get_def_folder()
    print fi.find_item(root + '395dc187673076cdba17557d12f94ce5.vcf')

def multi_get (cd, root):
    fi = cd.get_def_folder().find_items
    cs = fi(itemids=[root + '395dc187673076cdba17557d12f94ce5.vcf',
                     root + '7d69f2f10edb55e9ec15f99cdd321b88.vcf',
                     root + '8afb07c99deac51532a10a4070aa48ec.vcf'])

    for c in cs:
        print c
        print

def show_def_folder (cd, details=False):
    cd.get_def_folder().show(details)

def create_contact (cd):
    c = CDContact(cd.get_def_folder())
    c.set_firstname('Chalini')
    c.set_lastname('Tarantula')
    c.set_prefix('Dr.')
    c.set_suffix('Jr.')
    c.set_gender('Female')
    c.add_email_home('abcd1234@gmail.com')

    c.save()
    print c

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()

