#!/usr/bin/env python

## Copyright 2011 Sriram Karra <karra.etc@gmail.com>
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
## ####
##
## This is just a sample piece of code to test contact creation using extended
## MAPI.


import os, sys, logging
import winerror
from   win32com.mapi import mapi
from   win32com.mapi import mapitags

MOD_FLAG = mapi.MAPI_BEST_ACCESS

class mapiex:

    PSETID_Address_GUID = '{00062004-0000-0000-C000-000000000046}'

    def __init__ (self):
        logging.info('Logging in...')

        # initialize and log on
        mapi.MAPIInitialize(None)
        flags = mapi.MAPI_EXTENDED | mapi.MAPI_USE_DEFAULT | MOD_FLAG
        self.session = mapi.MAPILogonEx(0, "", None, flags)

        self.def_msgstore = self.def_inbox_id = self.def_inbox = None
        self.def_cf       = None

        self.def_msgstore = self.get_default_msgstore()
        self.def_inbox_id = self.get_default_inbox_id()
        self.def_inbox    = self.get_default_inbox()
        self.def_cf       = self.get_default_cf()

    def __del__ (self):
        self.session.Logoff(0, 0, 0)

    def get_default_msgstore (self):
        """Return the MAPI object corresponding to the default Message
           Store accessible from Extended MAPI"""

        if self.def_msgstore:
            return self.def_msgstore

        messagestorestable = self.session.GetMsgStoresTable(0)
        messagestorestable.SetColumns((mapitags.PR_ENTRYID,
                                       mapitags.PR_DISPLAY_NAME_A,
                                       mapitags.PR_DEFAULT_STORE),0)
    
        while True:
            rows = messagestorestable.QueryRows(1, 0)
            # if this is the last row then stop
            if len(rows) != 1:
                break
            row = rows[0]
            # if this is the default store then stop
            if ((mapitags.PR_DEFAULT_STORE,True) in row):
                break

        (eid_tag, eid), (name_tag, name), (def_store_tag, def_store) = row
        msgstore = self.session.OpenMsgStore(0, eid, None,
                                             mapi.MDB_NO_DIALOG | MOD_FLAG)
        return msgstore

    # FIXME: Error checking is virtually non-existent. Needs fixing.
    def get_default_inbox_id (self):
        """Return the EntryID for the Inbox folder from the default Message
            Store accessible from Extended MAPI"""

        if self.def_inbox_id:
            return self.def_inbox_id

        if self.def_msgstore is None:
            self.def_msgstore = self.get_default_msgstore()

        inbox_id, c = self.def_msgstore.GetReceiveFolder("IPM.Note", 0)
        return inbox_id

    # FIXME: Error checking is virtually non-existent. Needs fixing.
    def get_default_inbox (self):
        """Return the MAPI object for the Inbox folder in the default
           Message Store accessible from Extended MAPI"""

        if self.def_inbox:
            return self.def_inbox

        msgstore = self.def_msgstore
        if self.def_inbox_id is None:
            self.def_inbox_id = self.get_default_inbox_id()

        inbox = msgstore.OpenEntry(self.def_inbox_id, None, MOD_FLAG)
        return inbox

    # FIXME: Error checking is virtually non-existent. Needs fixing.
    def get_default_cf (self):
        """Returns a tuple (IMAPIFolder, IMAPITable) that can be used to
           manipulate the Contacts folder and the associated meta
           information"""

        if self.def_cf:
            return self.def_cf

        msgstore = self.get_default_msgstore()
        if self.def_inbox is None:
            self.def_inbox = self.get_default_inbox()

        PR_IPM_CONTACTS_ENTRYID = 0x36D10102
        hr, props = self.def_inbox.GetProps((PR_IPM_CONTACTS_ENTRYID), 0)
        (tag, cf_id) = props[0]
    
        # check for errors
        if mapitags.PROP_TYPE(tag) == mapitags.PT_ERROR:
            raise TypeError('got PT_ERROR: %16x' % tag)
        elif mapitags.PROP_TYPE(tag) == mapitags.PT_BINARY:
            pass

        cf = msgstore.OpenEntry(cf_id, None, MOD_FLAG)

        return cf

    def create_contact (self, name, email=None, org=None):
        """Save the current contact to Outlook, and returns the entryid of the
        entry."""

        logging.info('Saving to Outlook: %-32s ....', name)
        msg = self.def_cf.CreateMessage(None, 0)

        if not msg:
            return None

        self.props_list = [(mapitags.PR_MESSAGE_CLASS, "IPM.Contact")]
        self.props_list.append((mapitags.PR_DISPLAY_NAME, name))

        fileas_prop_tag = self.get_file_as_prop_tag()
        self.props_list.append((fileas_prop_tag, name))

        self.props_list.append((mapitags.PR_COMPANY_NAME, org))
        self.props_list.append((mapitags.PR_BODY, email))

        hr, res = msg.SetProps(self.props_list)
        if (winerror.FAILED(hr)):
            logging.critical('push_to_outlook(): unable to SetProps (code: %x)',
                             winerror.HRESULT_CODE(hr))
            return None

        msg.SaveChanges(mapi.KEEP_OPEN_READWRITE)

    def get_file_as_prop_tag (self):
        prop_name = [(self.PSETID_Address_GUID, 0x8005)]
        prop_type = mapitags.PT_UNICODE
        prop_ids = self.def_cf.GetIDsFromNames(prop_name, 0)

        return (prop_type | prop_ids[0])

def main (argv=None):
    logging.getLogger().setLevel(logging.DEBUG)

    DIR_PATH = os.path.abspath(os.path.dirname(os.path.realpath('Gout')))
    EXTRA_PATHS = [
        DIR_PATH,
        os.path.join(DIR_PATH, 'lib'),
        os.path.join(DIR_PATH, 'asynk'),
    ]
    sys.path = EXTRA_PATHS + sys.path

    logging.debug('Hello there..')

    m = mapiex()
    m.create_contact(name="Ronald Rumsfield",
                     email="ronald@usa.gov",
                     org='The Federal Government of the USA')

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()
