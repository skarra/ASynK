#!/usr/bin/env python

## Created	 : Wed May 18 13:16:17  2011
## Last Modified : Tue Jul 12 18:41:22  2011
##
## Copyright 2011 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
## 

## Status as of Mon Jul 11 12:24:38  2011
##
## We are able to create a Group on Google Contacts, and upload all our
## information to that group as new contacts.
##

import win32com.client
import pywintypes
from win32com.mapi import mapi
from win32com.mapi import mapitags

import demjson
import gdata.client
from gc_wrapper import GC

import logging, os, os.path

DEBUG = 0
gid = 'http://www.google.com/m8/feeds/groups/karra.etc%40gmail.com/base/5353d42d8d17504a'
gn  = 'Karra Sync'

PR_EMAIL_1 = mapitags.PR_EMAIL_ADDRESS
PR_EMAIL_2 = mapitags.PR_EMAIL_ADDRESS
PR_EMAIL_3 = mapitags.PR_EMAIL_ADDRESS

MOD_FLAG = mapi.MAPI_BEST_ACCESS

GC_GUID  = '{a1271100-ac2e-11e0-bc8b-0025644a821c}'
GC_ID    = 0x8001

## The following attempt is from:
## http://win32com.goermezer.de/content/view/97/192/
import codecs, win32com.client
# This example dumps the items in the default address book
# needed for converting Unicode->Ansi (in local system codepage)
DecodeUnicodeString = lambda x: codecs.latin_1_encode(x)[0]
def DumpDefaultAddressBook (handler=None):
    if handler is None:
        writer = getattr(logging, "debug")
    else:
        writer = handler.write

    # Create instance of Outlook
    o = win32com.client.Dispatch("Outlook.Application")
    mapi = o.GetNamespace("MAPI")
    folder = mapi.GetDefaultFolder(win32com.client.constants.olFolderContacts)
    print "The default address book contains",folder.Items.Count,"items"
    # see Outlook object model for more available properties on ContactItem objects
#    attributes = [ 'FullName', 'Email1DisplayName',
#    'Email1AddressType']
    attributes = ['Email1Address', 'EntryID',
                  'Email1EntryID']

    writer('<table border="1" align="left">')
    for i in range(1,folder.Items.Count+1):
#        writer("~~~ Entry %d ~~~" % i)
        if i >= 10:
            break

        try:
            item = folder.Items[i]
            print "~~~ Entry %d (%s) ~~~" % (i, item.FullName)
            ad = ''
            if item.Email1AddressType == 'EX':
                try:
#                    ae = mapi.GetAddressEntryFromID(item.Email1EntryID)
                    ad = item.Email1Address
                except Exception, e:
                    print 'Exception getting id: ', e
            else:
                ad = item.Email1Address
            writer("<tr>")
            writer("<th>")
            writer('%s: %s' % ('Full Name', item.FullName))
            writer("</th>")
            writer("<th>")
            writer('%s: %s' % ('Email', ad))
            writer("</th>")

        except AttributeError, e:
            print 'Error! ', e
        finally:
            writer("</td>")

        if handler:
            handler.flush()
    o = None
    writer("</table>")


class Contact:
    def __init__ (self, props, cf, msgstore):
        """Create a contact wrapper with meaningful fields from prop
        list.

        'props' is an array of (prop_tag, prop_value) tuples
        """
    
        self.PROP_REPLACE = 0
        self.PROP_APPEND  = 1

        self.gcapi = GC('karra.etc', 'atlsGL21')

        fields = get_sync_fields()
        fields = append_email_prop_tags(fields, cf)

        self.values = get_contact_details(cf, props, fields)

        self.cf        = cf
        self.msgstore  = msgstore

        self.entryid   = self._get_prop(mapitags.PR_ENTRYID)
        self.name      = self._get_prop(mapitags.PR_DISPLAY_NAME)
        self.postal    = self._get_prop(mapitags.PR_POSTAL_ADDRESS)
        self.notes     = self._get_prop(mapitags.PR_BODY)
        self.company   = self._get_prop(mapitags.PR_COMPANY_NAME)
        self.title     = self._get_prop(mapitags.PR_TITLE)
        self.dept      = self._get_prop(mapitags.PR_DEPARTMENT_NAME)
        self.ph_prim   = self._get_prop(mapitags.PR_PRIMARY_TELEPHONE_NUMBER)
        self.ph_mobile = self._get_prop(mapitags.PR_MOBILE_TELEPHONE_NUMBER)
        self.ph_home   = self._get_prop(mapitags.PR_HOME_TELEPHONE_NUMBER)
        self.ph_work   = self._get_prop(mapitags.PR_BUSINESS_TELEPHONE_NUMBER)

        ## Build an aray out of the three email addresses as applicable
        e = self._get_prop(PR_EMAIL_1)
        self.emails = [e] if e else None

        e = self._get_prop(PR_EMAIL_2)
        if e:
            if self.emails:
                self.emails.append(e)
            else:
                self.emails = [e]

        e = self._get_prop(PR_EMAIL_3)
        if e:
            if self.emails:
                self.emails.append(e)
            else:
                self.emails = [e]

        self.item = self.msgstore.OpenEntry(self.entryid, None,
                                            MOD_FLAG)


    def update_prop (self, prop_tag, prop_val, action):
        if self.item is None:
            self.item = self.msgstore.OpenEntry(self.entryid, None,
                                                MOD_FLAG)

        try:
            hr, props = self.item.GetProps([prop_tag, mapitags.PR_ACCESS,
                                            mapitags.PR_ACCESS_LEVEL],
                                           mapi.MAPI_UNICODE)
            (tag, val)        = props[0]

            if mapitags.PROP_TYPE(tag) == mapitags.PT_ERROR:
                logging.info('Prop (0x%16x) not found. Tag: 0x%16x',
                             prop_tag, tag)
                val = ''            # This could be an int. FIXME
            elif mapitags.PROP_TYPE(tag) == mapitags.PT_BINARY:
                pass

        except Exception, e:
            logging.info("Could not fetch the old value... (%s).",
                         e)
            val = ''            # This could be an int. FIXME

        if action == self.PROP_REPLACE:
            val = prop_val
        elif action == self.PROP_APPEND:
            val = '%s%s' % (val, prop_val)

        logging.debug('type of tag: %s', type(prop_tag))
        logging.debug('tag: 0x%16x', (prop_tag % (2**64)))
        logging.debug('type of val: %s', type(val))
        logging.debug('val: %s', val)

        try:
            hr, res = self.item.SetProps([(prop_tag, val)])
            self.item.SaveChanges(mapi.KEEP_OPEN_READWRITE)
        except Exception, e:
            logging.critical('Could not update property (0x%16x): %s',
                             prop_tag, e)
            raise


    def update_prop_by_name (self, prop_name, prop_type,
                             prop_val, action=None):
        """prop_name should be an array of (guid, index) tuples."""

        if action is None:
            action = self.PROP_REPLACE

        prop_ids = self.cf.GetIDsFromNames(prop_name, mapi.MAPI_CREATE)
        prop_tag = prop_type | prop_ids[0]

        return self.update_prop(prop_tag, prop_val, action)


    def _get_prop (self, prop_tag, array=False, values=None):
        if not values:
            values = self.values

        if not (prop_tag in values.keys()):
            return None

        if values[prop_tag]:
            if array:
                return values[prop_tag]

            if len(values[prop_tag]) > 0:
                return values[prop_tag][0]
            else:
                return None
        else:
            return None


    def push_to_google (self):
        MAX_RETRIES = 3

        logging.info('Uploading %-32s ....', self.name)

        i = 0
        entry = None
        while i < MAX_RETRIES:
            try:
                i += 1
                entry = self.gcapi.create_contact(entryid=self.entryid,
                                                  name=self.name,
                                                  emails=self.emails,
                                                  notes=self.notes,
                                                  postal=self.postal,
                                                  company=self.company,
                                                  title=self.title,
                                                  dept=self.dept,
                                                  ph_prim=self.ph_prim,
                                                  ph_mobile=self.ph_mobile,
                                                  ph_home=self.ph_home,
                                                  ph_work=self.ph_work
                                                  )
                i = MAX_RETRIES
            except Exception, e:
                ## Should make it a bit more granular
                logging.error('Exception (%s) uploading. Will Retry (%d)',
                              e, i)

        # Now store the Google Contacts ID in Outlook, so we'll be able
        # to compare the records from the two sources at a later time.
        self.update_prop_by_name([(GC_GUID, GC_ID)],
                                 mapitags.PT_UNICODE,
                                 entry.id.text)


    def verify_google_id (self):
        """Internal Test function to check if tag storage works.

        This is intended to be used for debug to retrieve and print the
        value of the Google Contacts Entry ID that is stored in MS
        Outlook.
        """

        prop_name = [(GC_GUID, GC_ID)]
        prop_type = mapitags.PT_UNICODE
        prop_ids = self.cf.GetIDsFromNames(prop_name, 0)

        print 'verify_google_id: type of prop_id: ', type(prop_ids[0])
        prop_tag = prop_type | prop_ids[0]

        hr, props = self.item.GetProps([prop_tag], mapi.MAPI_UNICODE)
        (tag, val) = props[0]
        if mapitags.PROP_TYPE(tag) == mapitags.PT_ERROR:
            print 'Prop_Tag (0x%16x) not found. Tag: 0x%16x' % (prop_tag,
                                                                (tag % (2**64)))
        else:
            print 'Google ID found for contact. ID: ', val
                                  

## FIXME: Error checking is virtually non-existent. Needs fixing.
def get_default_msg_store ():
    """Return the MAPI object corresponding to the default Message
    Store accessible from Extended MAPI"""

   # initialize and log on
    mapi.MAPIInitialize(None)
    session = mapi.MAPILogonEx(0, "", None,
                               mapi.MAPI_EXTENDED | mapi.MAPI_USE_DEFAULT | MOD_FLAG)
    messagestorestable = session.GetMsgStoresTable(0)
    messagestorestable.SetColumns((mapitags.PR_ENTRYID,
                                   mapitags.PR_DISPLAY_NAME_A,
                                   mapitags.PR_DEFAULT_STORE),0)
    
    while True:
        rows = messagestorestable.QueryRows(1, 0)
        #if this is the last row then stop
        if len(rows) != 1:
            break
        row = rows[0]
        #if this is the default store then stop
        if ((mapitags.PR_DEFAULT_STORE,True) in row):
            break

    (eid_tag, eid), (name_tag, name), (def_store_tag, def_store) = row
    msgstore = session.OpenMsgStore(0, eid, None,
                                    mapi.MDB_NO_DIALOG | MOD_FLAG)

    return msgstore

## FIXME: Error checking is virtually non-existent. Needs fixing.
def get_default_inbox_id (msgstore=None):
    """Return the EntryID for the Inbox folder from the default Message
    Store accessible from Extended MAPI"""

    if msgstore is None:
        msgstore = get_default_msg_store()
    
    inbox_id, c = msgstore.GetReceiveFolder("IPM.Note", 0)

    return inbox_id, msgstore

## FIXME: Error checking is virtually non-existent. Needs fixing.
def get_default_inbox (inbox_id=None):
    """Return the MAPI object for the Inbox folder in the default
    Message Store accessible from Extended MAPI"""

    msgstore = None
    if inbox_id is None:
        inbox_id, msgstore = get_default_inbox_id(msgstore)

    #    hr, cf = msgstore.OpenEntry(inbox_id, mapi.MAPI_BEST_ACCESS | mapi.MAPI_MODIFY, 0)
    inbox = msgstore.OpenEntry(inbox_id, None,
                               MOD_FLAG)

    return inbox, msgstore

## FIXME: Error checking is virtually non-existent. Needs fixing.
def get_default_contacts_folder (inbox=None):
    """Returns a tuple (IMAPIFolder, IMAPITable) that can be used to
    manipulate the Contacts folder and the associated meta information"""
    msgstore = None
    if inbox is None:
        inbox, msgstore = get_default_inbox()

    PR_IPM_CONTACTS_ENTRYID = 0x36D10102
    hr, props = inbox.GetProps((PR_IPM_CONTACTS_ENTRYID), 0)
    (tag, cf_id) = props[0]
    
    # check for errors
    if mapitags.PROP_TYPE(tag) == mapitags.PT_ERROR:
        raise TypeError('got PT_ERROR instead of PT_BINARY: %16x' % tag)
    elif mapitags.PROP_TYPE(tag) == mapitags.PT_BINARY:
        pass

    cf = msgstore.OpenEntry(cf_id, None,
                            MOD_FLAG)
    contacts = cf.GetContentsTable(mapi.MAPI_UNICODE)

    return msgstore, cf, contacts

def get_sync_fields (fn="fields.json"):
    os.chdir(karra_cwd)
    
    fi = None
    try:
        fi = open(fn, "r")
    except IOError, e:
        logging.critical('Error! Could not Open file (%s): %s' % fn, e)
        return

    st = fi.read()
    o = demjson.decode(st)

    ar = []
    for field in o["sync_fields"]:
        try:
            v = getattr(mapitags, field)
            ar.append(v)
        except AttributeError, e:
            logging.error('Field %s not found', field)


    return ar


## FIXEME: Need to implement more robust error checking.
def append_email_prop_tags (fields, cf):
    """MAPI is crappy.

    Email addresses of the EX type do not conatain an SMTP address value
    for their PR_EMAIL_ADDRESS property tag. While the desired smtp
    address is present in the system the property tag that will help us
    fetch it is not a constant and will differ from system to system,
    and from PST file to PST file. The tag has to be dynamically
    generated.

    The routine jumps through the requisite hoops and appends those
    property tags to the supplied fields array. The augmented fields
    array is then returned.
    """

    PSETID_Address_GUID = '{00062004-0000-0000-C000-000000000046}'
    tag = cf.GetIDsFromNames([(PSETID_Address_GUID, 0x8084)])[0]
    tag = (long(tag) % (2**64)) | mapitags.PT_UNICODE

    global PR_EMAIL_1, PR_EMAIL_2, PR_EMAIL_3
    PR_EMAIL_1 = tag

    ## Now 'tag' contains the property tag that will give us the first
    ## email address.
    fields.append(tag)

    ## Now generate the property tags for the Email Address 2
    prop_id = ((tag & 0xffff0000) >> 16)
    tag = ((tag & 0xffffffff0000ffff) | ((prop_id+1) << 16))
    PR_EMAIL_2 = tag
    fields.append(tag)

    ## Do the same for Email Address 3
    prop_id = ((tag & 0xffff0000) >> 16)
    tag = ((tag & 0xffffffff0000ffff) | ((prop_id+1) << 16))
    PR_EMAIL_3 = tag
    fields.append(tag)

    return fields


## FIXEME: Need to implement more robust error checking.
def get_contact_details (cf, contact, fields):
    """Get all the values as per the tag ids mentioned in the fields
    parameter. 'Contact' is nothing but an array of (tag, value) pairs,
    that's it.

    Returns an hash of field => array of values for the property.
    """
    
    ar = {}
    for field in fields:
        ar[field] = []

    ## For starters, let's just look for one of them.    
    for t, v in contact:
        t = long(t % 2**64)
        if t in fields:
            ar[t].append(v)
    
    return ar

def print_prop (tag, value):
    prop_type = mapitags.PROP_TYPE(tag)
    prop_id   = mapitags.PROP_ID(tag)

    if prop_type & mapitags.MV_FLAG:
        print "Tag: 0x%16x (Multi Value); Value: %s" % (long(tag), value)
    else:
        print "Tag: 0x%16x; Value: %s" % (long(tag), value)


def print_all_props (contact):
    for t, v in contact:
        t = long(t % 2**64)
        print_prop(t, v)


def print_values (values):
    for k, v in values.items():
        logging.debug("Tag: 0x%16x; Value: %s",
                      long(k), v)


def m3 (argv = None):
    logging.getLogger().setLevel(logging.INFO)
    msgstore, cf, contacts = get_default_contacts_folder()

    i = 0
    while True:
        rows = contacts.QueryRows(1, 0)
        i += 1
        
        #if this is the last row then stop
        if len(rows) != 1:
            break

        try:
            contact = Contact(rows[0], cf, msgstore)
        except gdata.client.BadAuthentication, e:
            logging.critical('Invalid user credentials given: %s',
                             str(e))
            return
        except Exception, e:
            logging.critical('Exception (%s) at login time',
                             str(e))
            return

#        contact.update_prop(mapitags.PR_BODY,
#                            'Testing appending to Notes')
#        contact.push_to_google()
        contact.verify_google_id()

        if i >= 2:
            break

def main (argv=None):
    m3()

if __name__ == "__main__":
    main()
