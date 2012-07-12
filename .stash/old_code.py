#!/usr/bin/env python

## Created	 : Wed May 18 13:16:17  2011
## Last Modified : Sat May 12 10:43:34 IST 2012
##
## Copyright 2011 Sriram Karra <karra.etc@gmail.com>
##
## This file is part of ASynK
##
## ASynK is free software: you can redistribute it and/or modify it under
## the terms of the GNU Affero General Public License as published by the
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

import win32com.client
import pywintypes

DEBUG = 0

class MSOutlook:
    def __init__ (self):
        self.outlookFound = 0
        try:
            self.oOutlookApp = \
                win32com.client.gencache.EnsureDispatch("Outlook.Application")
            self.outlookFound = 1
        except:
            print "MSOutlook: unable to load Outlook"
        
        self.records = []


    def loadContacts (self, keys=None):
        if not self.outlookFound:
            return

        # this should use more try/except blocks or nested blocks
        onMAPI = self.oOutlookApp.GetNamespace("MAPI")
        ofContacts = \
            onMAPI.GetDefaultFolder(win32com.client.constants.olFolderContacts)

        if DEBUG:
            print "number of contacts:", len(ofContacts.Items)

        for oc in range(len(ofContacts.Items)):
            contact = ofContacts.Items.Item(oc + 1)
            if contact.Class == win32com.client.constants.olContact:
                if keys is None:
                    # if we were't give a set of keys to use
                    # then build up a list of keys that we will be
                    # able to process
                    # I didn't include fields of type time, though
                    # those could probably be interpreted
                    keys = []
                    for key in contact._prop_map_get_:
                        if isinstance(getattr(contact, key), (int, str, unicode)):
                            keys.append(key)
                    if DEBUG:
                        keys.sort()
                        print "Fields\n======================================"
                        for key in keys:
                            print key
                record = {}
                for key in keys:
                    record[key] = getattr(contact, key)
                if DEBUG:
                    print oc, record['FullName']
                self.records.append(record)

def use_class (argv = None):
    if DEBUG:
        print "attempting to load Outlook"
    oOutlook = MSOutlook()
    # delayed check for Outlook on win32 box
    if not oOutlook.outlookFound:
        print "Outlook not found"
        sys.exit(1)

    fields = ['FullName',
              'CompanyName', 
              'MailingAddressStreet',
              'MailingAddressCity', 
              'MailingAddressState', 
              'MailingAddressPostalCode',
              'HomeTelephoneNumber', 
              'BusinessTelephoneNumber', 
              'MobileTelephoneNumber',
              'Email1Address',
              'Body'
              ]

    if DEBUG:
        import time
        print "loading records..."
        startTime = time.time()

    # you can either get all of the data fields
    # or just a specific set of fields which is much faster
    #oOutlook.loadContacts()
    oOutlook.loadContacts(fields)
    if DEBUG:
        print "loading took %f seconds" % (time.time() - startTime)

    print "Number of contacts: %d" % len(oOutlook.records)
    print "Contact: %s" % oOutlook.records[0]['FullName']
    print "Body:\n%s" % oOutlook.records[0]['Body']

## The following attempt is from:
## http://win32com.goermezer.de/content/view/97/192/
import codecs, win32com.client
# This example dumps the items in the default address book
# needed for converting Unicode->Ansi (in local system codepage)
DecodeUnicodeString = lambda x: codecs.latin_1_encode(x)[0]
def DumpDefaultAddressBook_mod (handler=None):
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

## The following attempt is from:
## http://win32com.goermezer.de/content/view/97/192/

import codecs, win32com.client
# This example dumps the items in the default address book
# needed for converting Unicode->Ansi (in local system codepage)
DecodeUnicodeString = lambda x: codecs.latin_1_encode(x)[0]
def DumpDefaultAddressBook (writer):
    # Create instance of Outlook
    o = win32com.client.Dispatch("Outlook.Application")
    mapi = o.GetNamespace("MAPI")
    folder = mapi.GetDefaultFolder(win32com.client.constants.olFolderContacts)
    print "The default address book contains",folder.Items.Count,"items"
    # see Outlook object model for more available properties on ContactItem objects
    attributes = [ 'FullName', 'Email1DisplayName', 'Email1AddressType']
    for i in range(1,folder.Items.Count+1):
        writer("~~~ Entry %d ~~~" % i)
        item = folder.Items[i]
        for attribute in attributes:
            writer(attribute, eval('item.%s' % attribute))
    o = None

# Attempting modify. Let's hold on to this horse.
def m (argv = None):
    o = win32com.client.Dispatch("Outlook.Application")
    ns = o.GetNamespace("MAPI")
    profile = ns.Folders.Item("My Profile Name")
    contacts = profile.Folders.Item("Contacts")
    contact = contacts.Items[43] # Grab a random contact, for this example.
    print "About to overwrite ",contact.FirstName, contact.LastName
    contact.categories = 'Supplier' # Override the categories

    # Edit: I don't always do these last steps.
    ns = None 
    o = None

def main (argv=None):
    DumpDefaultAddressBook()

if __name__ == "__main__":
    main()

class MSOutlook:
    def __init__ (self):
        self.outlookFound = 0
        try:
            self.oOutlookApp = \
                win32com.client.gencache.EnsureDispatch("Outlook.Application")
            self.outlookFound = 1
        except:
            print "MSOutlook: unable to load Outlook"
        
        self.records = []


    def loadContacts (self, keys=None):
        if not self.outlookFound:
            return

        # this should use more try/except blocks or nested blocks
        onMAPI = self.oOutlookApp.GetNamespace("MAPI")
        ofContacts = \
            onMAPI.GetDefaultFolder(win32com.client.constants.olFolderContacts)

        if DEBUG:
            print "number of contacts:", len(ofContacts.Items)

        for oc in range(len(ofContacts.Items)):
            contact = ofContacts.Items.Item(oc + 1)
            if contact.Class == win32com.client.constants.olContact:
                if keys is None:
                    # if we were't give a set of keys to use
                    # then build up a list of keys that we will be
                    # able to process
                    # I didn't include fields of type time, though
                    # those could probably be interpreted
                    keys = []
                    for key in contact._prop_map_get_:
                        if isinstance(getattr(contact, key), (int, str, unicode)):
                            keys.append(key)
                    if DEBUG:
                        keys.sort()
                        print "Fields\n======================================"
                        for key in keys:
                            print key
                record = {}
                for key in keys:
                    record[key] = getattr(contact, key)
                if DEBUG:
                    print oc, record['FullName']
                self.records.append(record)

def use_class (argv = None):
    if DEBUG:
        print "attempting to load Outlook"
    oOutlook = MSOutlook()
    # delayed check for Outlook on win32 box
    if not oOutlook.outlookFound:
        print "Outlook not found"
        sys.exit(1)

    fields = ['FullName',
              'CompanyName', 
              'MailingAddressStreet',
              'MailingAddressCity', 
              'MailingAddressState', 
              'MailingAddressPostalCode',
              'HomeTelephoneNumber', 
              'BusinessTelephoneNumber', 
              'MobileTelephoneNumber',
              'Email1Address',
              'Body'
              ]

    if DEBUG:
        import time
        print "loading records..."
        startTime = time.time()

    # you can either get all of the data fields
    # or just a specific set of fields which is much faster
    #oOutlook.loadContacts()
    oOutlook.loadContacts(fields)
    if DEBUG:
        print "loading took %f seconds" % (time.time() - startTime)

    print "Number of contacts: %d" % len(oOutlook.records)
    print "Contact: %s" % oOutlook.records[0]['FullName']
    print "Body:\n%s" % oOutlook.records[0]['Body']

# Attempting modify. Let's hold on to this horse.
def m (argv = None):
    o = win32com.client.Dispatch("Outlook.Application")
    ns = o.GetNamespace("MAPI")
    profile = ns.Folders.Item("My Profile Name")
    contacts = profile.Folders.Item("Contacts")
    contact = contacts.Items[43] # Grab a random contact, for this example.
    print "About to overwrite ",contact.FirstName, contact.LastName
    contact.categories = 'Supplier' # Override the categories

    # Edit: I don't always do these last steps.
    ns = None 
    o = None


def SendEMAPIMail(Subject="", Message="", SendTo=None, SendCC=None, SendBCC=None, MAPIProfile=None):
    """Sends an email to the recipient using the extended MAPI interface
    Subject and Message are strings
    Send{To,CC,BCC} are comma-separated address lists
    MAPIProfile is the name of the MAPI profile"""

    # initialize and log on
    mapi.MAPIInitialize(None)
    session = mapi.MAPILogonEx(0, MAPIProfile, None, mapi.MAPI_EXTENDED | mapi.MAPI_USE_DEFAULT)
    messagestorestable = session.GetMsgStoresTable(0)
    messagestorestable.SetColumns((mapitags.PR_ENTRYID, mapitags.PR_DISPLAY_NAME_A, mapitags.PR_DEFAULT_STORE),0)

    while True:
        rows = messagestorestable.QueryRows(1, 0)
        #if this is the last row then stop
        if len(rows) != 1:
            break
        row = rows[0]
        #if this is the default store then stop
        if ((mapitags.PR_DEFAULT_STORE,True) in row):
            break

    # unpack the row and open the message store
    (eid_tag, eid), (name_tag, name), (def_store_tag, def_store) = row
    msgstore = session.OpenMsgStore(0,eid,None,mapi.MDB_NO_DIALOG | mapi.MAPI_BEST_ACCESS)

    # get the outbox
    hr, props = msgstore.GetProps((mapitags.PR_IPM_OUTBOX_ENTRYID), 0)
    (tag, eid) = props[0]
    #check for errors
    if mapitags.PROP_TYPE(tag) == mapitags.PT_ERROR:
        raise TypeError('got PT_ERROR instead of PT_BINARY: %s'%eid)
    outboxfolder = msgstore.OpenEntry(eid,None,mapi.MAPI_BEST_ACCESS)

    # create the message and the addrlist
    message = outboxfolder.CreateMessage(None,0)
    # note: you can use the resolveaddress functions for this. but you may get headaches
    pal = []
    def makeentry(recipient, recipienttype):
      return ((mapitags.PR_RECIPIENT_TYPE, recipienttype),
              (mapitags.PR_SEND_RICH_INFO, False),
              (mapitags.PR_DISPLAY_TYPE, 0),
              (mapitags.PR_OBJECT_TYPE, 6),
              (mapitags.PR_EMAIL_ADDRESS_A, recipient),
              (mapitags.PR_ADDRTYPE_A, 'SMTP'),
              (mapitags.PR_DISPLAY_NAME_A, recipient))
    
    if SendTo:
      pal.extend([makeentry(recipient, mapi.MAPI_TO) for recipient in SendTo.split(",")])
    if SendCC:
      pal.extend([makeentry(recipient, mapi.MAPI_CC) for recipient in SendCC.split(",")])
    if SendBCC:
      pal.extend([makeentry(recipient, mapi.MAPI_BCC) for recipient in SendBCC.split(",")])

    # add the resolved recipients to the message
    message.ModifyRecipients(mapi.MODRECIP_ADD,pal)
    message.SetProps([(mapitags.PR_BODY_A,Message),
                      (mapitags.PR_SUBJECT_A,Subject)])

    # save changes and submit
    outboxfolder.SaveChanges(0)
    message.SubmitMessage(0)

def m4 ():
   MAPIProfile = ""
   # Change this to a valid email address to test
   SendTo = "skarra@gmail.com"
   SendMessage = "testing one two three"
   SendSubject = "Testing Extended MAPI!!"
   SendEMAPIMail(SendSubject, SendMessage, SendTo, MAPIProfile=MAPIProfile)

#    contact = contacts.Items[43] # Grab a random contact
#    print "About to overwrite ",contact.FirstName, contact.LastName
#    contact.categories = 'Supplier' # Override the categories    
