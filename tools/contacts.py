#!/usr/bin/env python

## Created	 : Wed May 18 13:16:17  2011
## Last Modified : Mon Jul 11 14:43:07  2011
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
## TODO:
##
## 1. The postal address information is not getting uploaded
##    properly. There is no problem in reading it from the Outlook
##    addressbook. There is some problem in uploading it with the right
##    schema
##
## 2. More contact fields need to get synched, including: all the phone
##    fields (more than 1 Home), Fax, anniversary, IM, etc.
##
## 3. Store the ID of the newly created entry and store it in some field
##    in Outlook.
##
## 4. Figure out how updates to the Google contact list can be
##    recognized and synched.
##
## 5. There could be more than one message store in the default Outlook
##    Profile. Need to be able to look into all of them for contact
##    items.
##
##

import win32com.client
import pywintypes
from win32com.mapi import mapi
from win32com.mapi import mapitags

import demjson
from gc_wrapper import GC

import logging, os, os.path

DEBUG = 0
gid = 'http://www.google.com/m8/feeds/groups/karra.etc%40gmail.com/base/5353d42d8d17504a'
gn  = 'Karra Sync'

PR_EMAIL_1 = mapitags.PR_EMAIL_ADDRESS
PR_EMAIL_2 = mapitags.PR_EMAIL_ADDRESS
PR_EMAIL_3 = mapitags.PR_EMAIL_ADDRESS

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
    def __init__ (self, props, cf):
        """Create a contact wrapper with meaningful fields from prop
        list.

        'props' is an array of (prop_tag, prop_value) tuples
        """
    
        self.gcapi = None
        try:
            self.gcapi = GC('karra.etc', 'atlsGL21')
        except gdata.client.BadAuthentication, e:
            logging.critical('Invalid user credentials given: %s', e)
            return

        fields = get_sync_fields()
        fields = append_email_prop_tags(fields, cf)

        self.values = get_contact_details(cf, props, fields)

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
        while i < MAX_RETRIES:
            try:
                i += 1
                self.gcapi.create_contact(entryid=self.entryid,
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
                                  

## FIXME: Error checking is virtually non-existent. Needs fixing.
def get_default_msg_store ():
    """Return the MAPI object corresponding to the default Message
    Store accessible from Extended MAPI"""

   # initialize and log on
    mapi.MAPIInitialize(None)
    session = mapi.MAPILogonEx(0, "", None,
                               mapi.MAPI_EXTENDED | mapi.MAPI_USE_DEFAULT)
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
    msgstore = session.OpenMsgStore(0, eid, None, mapi.MDB_NO_DIALOG)

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
    inbox = msgstore.OpenEntry(inbox_id, None, 0)

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
        raise TypeError('got PT_ERROR instead of PT_BINARY: %16x' % eid)
    elif mapitags.PROP_TYPE(tag) == mapitags.PT_BINARY:
        pass

    cf = msgstore.OpenEntry(cf_id, None, 0)
    contacts = cf.GetContentsTable(mapi.MAPI_UNICODE)

    return cf, contacts

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
    cf, contacts = get_default_contacts_folder()

    i = 0
    while True:
        rows = contacts.QueryRows(1, 0)
        i += 1
        
        #if this is the last row then stop
        if len(rows) != 1:
            break

        contact = Contact(rows[0], cf)
        contact.push_to_google()

        if i >= 2:
            break

def main (argv=None):
    m3()

if __name__ == "__main__":
    main()
