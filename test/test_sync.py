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

import getopt, logging, os, os.path, sys, traceback

## Being able to fix the sys.path thusly makes is easy to execute this
## script standalone from IDLE. Hack it is, but what the hell.
DIR_PATH    = os.path.abspath(os.path.dirname(os.path.realpath('../Gout')))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk')]
sys.path = EXTRA_PATHS + sys.path

from   pimdb_bb         import BBPIMDB
from   sync             import Sync
from   state            import Config
import utils

from   gdata.client     import BadAuthentication
from   pimdb_gc         import GCPIMDB
import atom, gdata, gdata.client
import gdata.contacts.data, gdata.contacts.client


def main ():
    tests = TestSync('bb', 'gc')

    #tests.test_sync_status()
    tests.test_sync()

    # tests.test_clear_ol_sync_flags()

    # tests.del_gcid('AAAAADWE5+lnNclLmn8GpZUD04fEQGMA')
    # tests.read_gcid('AAAAADWE5+lnNclLmn8GpZUD04ekQGMA')

class TestSync:
    def __init__ (self, db1, db2=None, dirn=None):
        self.config = Config('../app_state.json')

        if 'ol' in [db1, db2]:
            from   pimdb_ol         import OLPIMDB
            from   contact_ol       import OLContact
            from   win32com.mapi    import mapi, mapitags
            import winerror

        self.db1id = db1
        self.db2id = db2

        login_func = '_login_%s' % db1
        self.db1 = getattr(self, login_func)()

        if db2:
            login_func = '_login_%s' % db2
            self.db2 = getattr(self, login_func)()
        else:
            self.db2 = None

    def _login_bb (self):
        if len(sys.argv) > 1:
            bbfn = sys.argv[1]
        else:
            bbfn = '/Users/sriramkarra/.bbdb.t'

        self.bb  = BBPIMDB(self.config, bbfn)
        self.bbf = self.bb.get_def_folder()

        return self.bb

    def _login_gc (self):
        # Parse command line options
        try:
            opts, args = getopt.getopt(sys.argv[1:], '', ['user=', 'pw='])
        except getopt.error, msg:
            print 'python gc_wrapper.py --user [username] --pw [password]'
            sys.exit(2)

        user = ''
        pw = ''
        # Process options
        for option, arg in opts:
            if option == '--user':
                user = arg
            elif option == '--pw':
                pw = arg

        while not user:
            user = raw_input('Please enter your username: ')

        while not pw:
            pw = raw_input('Password: ')
            if not pw:
                print 'Password cannot be blank'

        try:
            self.pimgc = GCPIMDB(self.config, user, pw)
        except BadAuthentication:
            print 'Invalid credentials. WTF.'
            raise

        destid = self.db2id if self.db1id == 'gc' else self.db1id
        logging.debug('Google destid is: %s', destid)

        gn = '%s%s%s' % (self.config.get_label_prefix(),
                         self.config.get_label_separator(),
                         destid)

        self.gid = self.config.get_group_ids(self.db1id, self.db2id, 'gc',
                                             gn)
        if not self.gid:
            ## We need to create a new group
            logging.debug('Sync group on Google not set up for %s. Creatng...',
                          destid)
            self.gid = self.pimgc.new_folder(gn)
            self.config.set_group_ids(self.db1id, self.db2id, 'gc', gn,
                                      self.gid)
        return self.pimgc

    def _login_ol (self):
        self.pimol = OLPIMDB(self.config)
        return self.pimol

    def del_gcid (self, itemid):
        ## This should really go into contact_ol.py
        olcf     = self.pimol.get_def_folder()
        eid      = base64.b64decode(itemid)
        
        prop_tag = olcf.get_proptags().valu('ASYNK_PR_GCID')
        store    = olcf.get_msgstore()
        item     = store.get_obj().OpenEntry(eid, None, mapi.MAPI_BEST_ACCESS)

        hr, ps = item.DeleteProps([prop_tag])
        item.SaveChanges(mapi.KEEP_OPEN_READWRITE)

        if winerror.FAILED(hr):
            logging.info('Failed to clear GCID for itemid: %s (%s)',
                         itemid, winerror.HRESULT_CODE(hr))
        else:
            logging.info('Successfully Cleared GCID for itemid: %s', itemid)

    def read_gcid (self, itemid):
        ## This should really go into contact_ol.py
        olcf     = self.pimol.get_def_folder()
        eid      = base64.b64decode(itemid)

        prop_tag = olcf.get_proptags().valu('ASYNK_PR_GCID')
        store    = olcf.get_msgstore()
        item     = store.get_obj().OpenEntry(eid, None, mapi.MAPI_BEST_ACCESS)

        hr, props = item.GetProps([prop_tag], mapi.MAPI_UNICODE)
        (tag, val) = props[0]
        if mapitags.PROP_TYPE(tag) == mapitags.PT_ERROR:
            print 'Prop_Tag (0x%16x) not found. Tag: 0x%16x' % (prop_tag,
                                                                (tag % (2**64)))
        else:
            print 'Google ID found for contact. ID: ', val

    def test_sync_status (self):
        db1cf = self.db1.get_def_folder()
        db2cf = self.find_group(self.gid)

        self.sync = Sync(self.config, db1cf, db2cf)
        self.sync._prep_lists()

    def test_sync_status_old (self):
        olcf = self.pimol.get_def_folder()
        gccf = self.find_group(self.gid)

        self.sync = Sync(self.config, gccf, olcf)
        self.sync._prep_lists()

    def test_sync (self):
        logging.debug('test_sync()... Starting Sync...')
        db1cf = self.db1.get_def_folder()
        db2cf = self.find_group(self.gid)

        self.sync = Sync(self.config, db1cf, db2cf)

        sl1, sl2 = self.sync._prep_lists()
        sl1.sync_to_folder(db2cf)
        # sl2.sync_to_folder(db1cf)

        logging.debug('test_sync()... Finished Sync')

    def test_clear_ol_sync_flags (self):
        olcf = self.pimol.get_def_folder()
        olcf.bulk_clear_sync_flags(['bb', 'gc'])

    def find_group (self, gid):
        gc, ftype = self.pimgc.find_folder(gid)
        if gc:
            print 'Found the sucker. Name is: ', gc.get_name()
            return gc
        else:
            print 'D''oh. Folder not found.'
            return

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    try:
        main()
    except Exception, e:
        print 'Caught Exception... Hm. Need to cleanup.'
        print 'Full Exception as here:', traceback.format_exc()

