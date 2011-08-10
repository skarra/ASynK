#!/usr/bin/env python

## Created	 : Mon Jun 20 12:12:56  2011
## Last Modified : Mon Jun 20 12:13:20  2011
##
## Copyright 2011 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3

#!/usr/bin/env python

## Created	 : Wed May 18 13:16:17  2011
## Last Modified : Mon May 30 19:11:00  2011
##
## Copyright 2011 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
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
def DumpDefaultAddressBook (handler=None):
    if handler is None:
        writer = "print"
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
        if i >= 200:
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
#            for attribute in attributes:
#                writer('%s: %s ' % (attribute,eval('item.%s' % attribute)))
        except AttributeError, e:
            print 'Error! ', e
        finally:
            writer("</td>")

        if handler:
            handler.flush()
    o = None
    writer("</table>")

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
