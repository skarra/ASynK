##
## Created : Mon Apr 09 14:54:10 IST 2012
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

import logging, os, os.path, sys, traceback

## Being able to fix the sys.path thusly makes is easy to execute this
## script standalone from IDLE. Hack it is, but what the hell.
DIR_PATH    = os.path.abspath(os.path.dirname(os.path.realpath('../Gout')))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk')]
sys.path = EXTRA_PATHS + sys.path


import base64
from   win32com.mapi  import mapi, mapiutil
from   win32com.mapi  import mapitags as mt
from   sync       import SyncLists
from   state      import Config
from   pimdb_ol   import OLPIMDB
from   contact_ol import OLContact

def main (argv=None):
    tests = TestOLContact()
    
    # tests.print_contact("AAAAADWE5+lnNclLmn8GpZUD04fE1mMA")
    # print '---'
    # tests.print_contact("AAAAADWE5+lnNclLmn8GpZUD04dE12MA")

    # tests.test_read_custom_props("AAAAADWE5+lnNclLmn8GpZUD04fE1mMA")

    # tests.test_fields_in_props("AAAAADWE5+lnNclLmn8GpZUD04fE1mMA")

    tests.test_fields_in_props("AAAAADWE5+lnNclLmn8GpZUD04ek1mMA")
    # tests.test_read_emails('AAAAADWE5+lnNclLmn8GpZUD04fE7C0A')
    # tests.test_new_contact()
    # tests.test_sync_status()

class TestOLContact:
    def __init__ (self):
        logging.debug('Getting started... Reading Config File...')

        self.config = Config('../config.json', '../state.json')
        self.ol     = OLPIMDB(self.config)
        self.deff   = self.ol.get_def_folder()

        print "\nHurrah: Name is: ", self.deff.get_name()

    def print_contact (self, itemid):
        eid = base64.b64decode(itemid)
        c = OLContact(self.deff, eid=eid)
        logging.debug('Contact: \n%s', str(c))        

    def test_new_contact (self):
        c = OLContact(self.deff)
        c.set_name('Supeman')
        c.set_gender('Male')
        c.set_notes('This is a second test contact')
        c.save()

    def test_fields_in_props (self, itemid):
        """Check if the the properties returned by a default search
        include all the fields that the user has requested for through
        the fields.json file. This is intended to be used for
        development and debugging purposes."""

        if not itemid:
            itemid = self.get_itemid()

        con = OLContact(self.deff, eid=base64.b64decode(itemid))

        print 'Con: \n', con

        props  = dict(con.get_olprops_from_mapi()) # later to try get_olprops_from_mapi
        fields = con.get_sync_fields()
        pt     = self.deff.get_proptags()

        logging.debug('Type of props        : %s', type(props))
        logging.debug('Num props in props   : %d', len(props))
        logging.debug('Num fields in fields : %d', len(fields))

        for tag in props:
            props[tag]= True

        for field in fields:
            if not field in props.keys():
                logging.debug('Property %35s (0x%x) not in Props.',
                             pt.name(field), field)
            else:
                logging.debug('Property %35s (0x%x)     in Props.',
                              pt.name(field), field)

    def test_read_custom_props (self, itemid):
        eid = base64.b64decode(itemid)
        olcf = self.deff
        
        prop_tag = olcf.get_proptags().get_custom_prop_tag()
        store    = olcf.get_msgstore()
        item     = store.get_obj().OpenEntry(eid, None, mapi.MAPI_BEST_ACCESS)

        hr, props = item.GetProps([prop_tag], mapi.MAPI_UNICODE)
        (tag, val) = props[0]
        if mt.PROP_TYPE(tag) == mt.PT_ERROR:
            print 'Prop_Tag (0x%16x) not found. Tag: 0x%16x' % (prop_tag,
                                                                (tag % (2**64)))
        else:
            print 'Hurrah! Custom found: ', val

    def test_read_emails (self, itemid):
        eid = base64.b64decode(itemid)
        olcf = self.deff
        
        prop_tag = olcf.get_proptags().valu('ASYNK_PR_EMAIL_1')
        store    = olcf.get_msgstore()
        item     = store.get_obj().OpenEntry(eid, None, mapi.MAPI_BEST_ACCESS)

        hr, props = item.GetProps([prop_tag], mapi.MAPI_UNICODE)
        (tag, val) = props[0]
        if mt.PROP_TYPE(tag) == mt.PT_ERROR:
            print 'Prop_Tag (0x%16x) not found. Tag: 0x%16x' % (prop_tag,
                                                                (tag % (2**64)))
        else:
            print 'Email address found: ', val

    def test_sync_status (self):
        sl = SyncLists(self.deff, 'gc')
        self.deff.prep_sync_lists('gc', sl)

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    try:
        main()
    except Exception, e:
        print 'Caught Exception... Hm. Need to cleanup.'
        print 'Full Exception as here:', traceback.format_exc()

## FIXME: Needs more thorough unit testing.
