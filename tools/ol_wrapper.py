#!/usr/bin/env python

## Created	 : Wed May 18 13:16:17  2011
## Last Modified : Thu Aug 25 20:48:42  2011
##
## Copyright 2011 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
## 

import win32com.client
import pywintypes
from   win32com.mapi import mapi
from   win32com.mapi import mapitags
from   win32com.mapi import mapiutil
import winerror

import demjson
import gdata.client
import gdata.contacts.client
import iso8601
import base64

from   gc_wrapper import get_udp_by_key
import utils

import logging, os, os.path
import time
from   datetime import datetime

DEBUG = 0

PR_EMAIL_1 = mapitags.PR_EMAIL_ADDRESS
PR_EMAIL_2 = mapitags.PR_EMAIL_ADDRESS
PR_EMAIL_3 = mapitags.PR_EMAIL_ADDRESS

MOD_FLAG = mapi.MAPI_BEST_ACCESS

class Outlook:
    def __init__ (self, config):
        self.config = config

        # initialize and log on
        mapi.MAPIInitialize(None)
        flags = mapi.MAPI_EXTENDED | mapi.MAPI_USE_DEFAULT | MOD_FLAG
        self.session = mapi.MAPILogonEx(0, "", None, flags)

        self.def_msgstore = self.def_inbox_id = self.def_inbox = None
        self.def_cf       = self.contacts     = self.gid_prop_tag = None

        self.def_msgstore = self.get_default_msgstore()
        self.def_inbox_id = self.get_default_inbox_id()
        self.def_inbox    = self.get_default_inbox()
        self.def_cf       = self.get_default_cf()
        self.def_ctable   = self.get_ctable(self.def_cf)

        self.gid_prop_tag = self.get_gid_prop_tag()
        self.def_ctable_cols = self.def_ctable.QueryColumns(0) + (self.gid_prop_tag,)


    def get_gid_prop_tag (self):
        if self.gid_prop_tag:
            return self.gid_prop_tag

        prop_name = [(self.config.get_gc_guid(),
                      self.config.get_gc_id())]
        prop_type = mapitags.PT_UNICODE
        prop_ids  = self.def_cf.GetIDsFromNames(prop_name, 0)

        return (prop_type | prop_ids[0])

    # FIXME: Error checking is virtually non-existent. Needs fixing.
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

    def get_ctable (self, cf=None):
        if cf is None:
            cf = self.get_default_cf()

        ctable = cf.GetContentsTable(mapi.MAPI_UNICODE)
        return ctable

    def get_default_ctable (self):
        if self.def_ctable:
            return self.def_ctable

        return self.get_ctable()

    def print_fields_for_contacts (self, cnt, fields=None):
        ctable = self.get_default_ctable()
        ctable.SetColumns(self.def_ctable_cols, 0)

        i = 0

        while True:
            rows = ctable.QueryRows(1, 0)
            #if this is the last row then stop
            if len(rows) != 1:
                break

            if fields is None:
                print_all_props(rows[0])
            else:
                # Just print what is in the fields. To be impl.
                pass

            i += 1

            if i >= cnt:
                break

        print 'num processed: ', i

        return


    def reset_sync_lists (self):
        self.con_all = {}
        self.con_new = []
        self.con_mod = {}
        
    def get_con_new (self):
        return self.con_new

    def get_con_mod (self):
        return self.con_mod

    def del_dict_items (self, d, l, keys=True):
        """Delete all the elements in d that match the elements in list
        l. If 'keys' is True the match is done on the keys of d, else
        match is done on the values of d"""
        
        # Don't you love python - all the compactness of Perl less all
        # the chaos
        if keys:
            d = dict([(x,y) for x,y in d.iteritems() if not x in l])
        else:
            d = dict([(x,y) for x,y in d.iteritems() if not y in l])

        return d

    def del_con_mod_by_keys (self, ary):
        """Remove all entries in thr con_mod dictionary whose keys
        appear in the 'ary' list."""

        self.con_mod = self.del_dict_items(self.con_mod, ary)

    def prep_ol_contact_lists (self, cnt=0):
        """Prepare three lists of the contacts in the local OL.

        1. dictionary of all Google IDs => PR_ENTRYIDs
        2. List of entries created after the last sync
        3. List of entries modified after the last sync
        """

        logging.info('Querying MAPI for status of Contact Entries')
        ctable = self.get_default_ctable()
        ctable.SetColumns((self.get_gid_prop_tag(),
                           mapitags.PR_ENTRYID,
                           mapitags.PR_LAST_MODIFICATION_TIME),
                          0)

        i   = 0
        old = 0
        self.reset_sync_lists()

        synct_str = self.config.get_last_sync_start()
        synct     = iso8601.parse(synct_str)
        print 'Last Start iso str: ', synct_str
        print 'Curr Time: ', iso8601.tostring(time.time())

        logging.info('Data obtained from MAPI. Processing...')

        while True:
            rows = ctable.QueryRows(1, 0)
            #if this is the last row then stop
            if len(rows) != 1:
                break
    
            (gid_tag, gid), (entryid_tag, entryid), (tt, modt) = rows[0]
            self.con_all[entryid] = gid

            if mapitags.PROP_TYPE(gid_tag) == mapitags.PT_ERROR:
                # Was not synced for whatever reason.
                self.con_new.append(entryid)
            else:
                if mapitags.PROP_TYPE(tt) == mapitags.PT_ERROR:
                    print 'Somethin wrong. no time stamp. i=', i
                else: 
                    if utils.utc_time_to_local_ts(modt) <= synct:
                        old += 1
                    else:
                        self.con_mod[entryid] = gid

            i += 1
            if cnt != 0 and i >= cnt:
                break

        print '==== OL ====='
        print 'num processed: ', i
        print 'num total:     ', len(self.con_all.items())
        print 'num new:       ', len(self.con_new)
        print 'num mod:       ', len(self.con_mod)
        print 'num old unmod: ', old

    def bulk_clear_gcid_flag (self):
        """Clear any gcid tags that are stored in Outlook. This is
        essentially for use while developin and debugging, when we want
        to make it appear like contact entries were never synched to
        google. This rolls back some sync related state on the outlook
        end.

        Need to explore if there is a faster way than iterating through
        entries after a table lookup.
        """
        logging.info('Querying MAPI for all data needed to clear flag')

        ctable = self.get_default_ctable()
        ctable.SetColumns((self.get_gid_prop_tag(), mapitags.PR_ENTRYID),
                           0)
        logging.info('Data obtained from MAPI. Clearing one at a time')

        cnt = 0
        i   = 0
        store = self.get_default_msgstore()
        hr = ctable.SeekRow(mapi.BOOKMARK_BEGINNING, 0)
        logging.debug('result of seekrow = %d', hr)

        while True:
            rows = ctable.QueryRows(1, 0)
            # if this is the last row then stop
            if len(rows) != 1:
                break
    
            (gid_tag, gid), (entryid_tag, entryid) = rows[0]

            i += 1
            if mapitags.PROP_TYPE(gid_tag) != mapitags.PT_ERROR:
                entry = store.OpenEntry(entryid, None, MOD_FLAG)
                hr, ps = entry.DeleteProps([gid_tag])
                entry.SaveChanges(mapi.KEEP_OPEN_READWRITE)

                cnt += 1

        logging.info('Num entries cleared: %d. i = %d', cnt, i)
        return cnt


class Contact:
    def __init__ (self, fields, config, props, ol, gcapi=None,
                  entryid=None, gcentry=None, data_from_ol=True):
        """Create a contact wrapper with meaningful fields from prop
        list.

        If gcentry is not None, then it has to be of type ContactEntry,
        typically obtained from a query to Google. If it is not None,
        values of props and entryid are ignored. Value of 'data_from_ol'
        is relevant in this case: If True, it is expected that a outlook
        entry is available, and data from outlook is used to override
        fie;ds from gcentry. If False, gcentry data items overwrite
        outlook.

        If gcentry is None, and props is None, entryid can be specified
        as the PR_ENTRYID of a contact. Alternately 'props' can be an
        array of (prop_tag, prop_value) tuples.

        One of these three has to be non-None.

        FIXME:
        The current constructor is a mess. This was envisoned as a
        generic wrapper to both a Outlook and Google contact entry. It
        is quite ugly; the design of the wrappers can and needs to be
        cleaned up.
        """

        self.config = config
        self.ol     = ol
        self.gcapi  = gcapi

        self.cf       = ol.get_default_cf()
        self.msgstore = ol.get_default_msgstore()

        self.PROP_REPLACE = 0
        self.PROP_APPEND  = 1

        self.gc_entry  = self.ol_item = None
        self.fields = fields
        self.fields = self.append_email_prop_tags(self.fields, self.cf)
        self.fields.append(self.ol.get_gid_prop_tag())

        etag = None
        if gcentry:
            # We are building a contact entry from a ContactEntry,
            # possibly retrieved from a query to google.
            self.data_from_ol = data_from_ol

            if data_from_ol:
                # Clear the gc_entry of everything except the wrapper ID
                # tags...
                etag = gcentry.etag
                olid_b64 = get_udp_by_key(gcentry.user_defined_field,
                                          'olid')
                entryid = base64.b64decode(olid_b64)
            else:
                # This is the Google to Outlook case. Yet to be
                # implemented
                self.gc_entry = gcentry
                props   = self.create_props_list(gcentry)
                print props
                entryid = None

        if entryid:
            self.entryid = entryid
            self.ol_item = self.get_ol_item()
            hr, props = self.ol_item.GetProps(self.ol.def_ctable_cols, 0)
            # FIXME: error checking needed

        ## fixme: catch error when both are None

        self.props = get_contact_details(self.cf, props, self.fields)
        self.populate_fields_from_props()

        self.gc_entry = self.get_gc_entry()
        if etag:
            self.gc_entry.etag = etag

#        self.check_fields_in_props()


    def check_fields_in_props (self):
        """Check if the the properties returned by a default search
        include all the fields that the user has requested for through
        the fields.json file. This is intended to be used for
        development and debugging purposes."""

        props = {}
        logging.debug('Type of self.props: %s', type(self.props))
        logging.debug('Num props in self.props   : %d', len(self.props))
        logging.debug('Num fields in fields.json : %d', len(self.fields))

        for tag in self.props:
            props[tag]= True

        for field in self.fields:
            if not field in props.keys():
                logging.debug('Property 0x%x not in Props.',
                              field)

    def populate_fields_from_props (self):
        self.entryid   = self._get_prop(mapitags.PR_ENTRYID)
        self.name      = self._get_prop(mapitags.PR_DISPLAY_NAME)
        self.last_mod  = self._get_prop(mapitags.PR_LAST_MODIFICATION_TIME)
        self.postal    = self._get_prop(mapitags.PR_POSTAL_ADDRESS)
        self.notes     = self._get_prop(mapitags.PR_BODY)
        self.company   = self._get_prop(mapitags.PR_COMPANY_NAME)
        self.title     = self._get_prop(mapitags.PR_TITLE)
        self.dept      = self._get_prop(mapitags.PR_DEPARTMENT_NAME)
        self.ph_prim   = self._get_prop(mapitags.PR_PRIMARY_TELEPHONE_NUMBER)
        self.ph_mobile = self._get_prop(mapitags.PR_MOBILE_TELEPHONE_NUMBER)
        self.ph_home   = self._get_prop(mapitags.PR_HOME_TELEPHONE_NUMBER)
        self.ph_home2  = self._get_prop(mapitags.PR_HOME2_TELEPHONE_NUMBER)
        self.ph_work   = self._get_prop(mapitags.PR_BUSINESS_TELEPHONE_NUMBER)
        self.ph_work2  = self._get_prop(mapitags.PR_BUSINESS2_TELEPHONE_NUMBER)
        self.ph_other  = self._get_prop(mapitags.PR_OTHER_TELEPHONE_NUMBER)
        self.fax_prim  = self._get_prop(mapitags.PR_PRIMARY_FAX_NUMBER)
        self.fax_work  = self._get_prop(mapitags.PR_BUSINESS_FAX_NUMBER)
        self.fax_home  = self._get_prop(mapitags.PR_HOME_FAX_NUMBER)

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

        self.gcid = self._get_prop(self.ol.get_gid_prop_tag())


    def create_props_list (self, ce, gcid_tag=None):
        """ce has to be an object of type ContactEntry. This routine
        forms and returns an array of tuples that can be passed to
        SetProps() of MAPI

        gcid_tag is the named property tag used to store the gcid.
        """

        props = []
        if gcid_tag is None:
            gcid_tag = self.ol.get_gid_prop_tag()

        if ce.name:
            props.append((mapitags.PR_DISPLAY_NAME, ce.name.text))

        if ce.content:
            props.append((mapitags.PR_BODY, ce.content.text))

        if ce.link:
            gcid = utils.get_link_rel(ce.link, 'edit')
            props.append((gcid_tag, gcid))

        # Email addresses. Need to figure out how primary email
        # addresses are tracked in MAPI
        if ce.email:
            if len(ce.email) > 0:
                props.append((PR_EMAIL_1, ce.email[0].address))
            if len(ce.email) > 1:
                props.append((PR_EMAIL_2, ce.email[1].address))
            if len(ce.email) > 2:
                props.append((PR_EMAIL_3, ce.email[2].address))

        if ce.organization:
            if ce.organization.name:
                value = ce.organization.name.text
                props.append((mapitags.PR_COMPANY, value))
            if ce.organization.title:
                value = ce.organization.title.text
                props.append((mapitags.PR_TITLE, value))
            if ce.organization.department:
                value = ce.organization.department.text
                props.append((mapitags.PR_DEPARTMENT_NAME, value))

        # Phone numbers. Need to figure out how primary phone numbers
        # are tracked in MAPI
        if ce.phone_number:
            hcnt = bcnt = 0
            har = [mapitags.PR_HOME_TELEPHONE_NUMBER,
                   mapitags.PR_HOME2_TELEPHONE_NUMBER]
            bar = [mapitags.PR_BUSINESS_TELEPHONE_NUMBER,
                   mapitags.PR_BUSINESS2_TELEPHONE_NUMBER]

            for ph in ce.phone_number:
                # There is only space for 2 work and 2 home numbers in
                # Outlook ... We will just keep overwriting the second
                # number. FIXME: could potentially do something smarter
                # here
                if ph.rel == gdata.data.HOME_REL:
                    props.append((har[hcnt], ph.text))
                    hcnt += (1 if hcnt < 1 else 0)
                elif ph.rel == gdata.data.WORK_REL:
                    props.append((bar[bcnt], ph.text))
                    bcnt += (1 if bcnt < 1 else 0)
                elif ph.rel == gdata.data.OTHER_REL:
                    props.append((mapitags.PR_OTHER_TELEPHONE_NUMBER,
                                  ph.text))
                elif ph.rel == gdata.data.MOBILE_REL:
                    props.append((mapitags.PR_MOBILE_TELEPHONE_NUMBER,
                                  ph.text))

                if ph.primary == 'true':
                    props.append((mapitags.PR_PRIMARY_TELEPHONE_NUMBER,
                                  ph.text))

        return props

    def get_ol_item (self):
        if self.ol_item is None:
            self.ol_item = self.msgstore.OpenEntry(self.entryid, None,
                                                MOD_FLAG)

        return self.ol_item


    def set_gcapi (self, gcapi):
        self.gcapi = gcapi


    def update_prop (self, prop_tag, prop_val, action):
        self.ol_item = self.get_ol_item()

        try:
            hr, props = self.ol_item.GetProps([prop_tag, mapitags.PR_ACCESS,
                                            mapitags.PR_ACCESS_LEVEL],
                                           mapi.MAPI_UNICODE)
            (tag, val)        = props[0]

            if mapitags.PROP_TYPE(tag) == mapitags.PT_ERROR:
                logging.debug('Prop (0x%16x) not found. Tag: 0x%16x',
                              prop_tag, tag)
                val = ''            # This could be an int. FIXME
        except Exception, e:
            logging.info("Could not fetch the old value... (%s).",
                         e)
            val = ''            # This could be an int. FIXME

        if action == self.PROP_REPLACE:
            val = prop_val
        elif action == self.PROP_APPEND:
            val = '%s%s' % (val, prop_val)

        try:
            hr, res = self.ol_item.SetProps([(prop_tag, val)])
            self.ol_item.SaveChanges(mapi.KEEP_OPEN_READWRITE)
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


    def _get_prop (self, prop_tag, array=False, props=None):
        if not props:
            props = self.props

        if not (prop_tag in props.keys()):
            return None

        if props[prop_tag]:
            if array:
                return props[prop_tag]

            if len(props[prop_tag]) > 0:
                return props[prop_tag][0]
            else:
                return None
        else:
            return None


    def get_gc_entry (self):
        """Create and return a gdata.contacts.data.ContactEntry
        object from the underlying contact properties"""

        if self.gc_entry:
            return self.gc_entry

        gids = [self.config.get_gid()]
        self.gc_entry = self.gcapi.create_contact_entry(
            entryid=self.entryid, name=self.name,     emails=self.emails,
            notes=self.notes,     postal=self.postal, company=self.company,
            title=self.title,     dept=self.dept,     ph_prim=self.ph_prim,
            ph_mobile=self.ph_mobile, ph_home=self.ph_home,
            ph_home2=self.ph_home2, ph_other=self.ph_other,
            ph_work=self.ph_work, ph_work2=self.ph_work2,
            fax_home=self.fax_home, fax_work=self.fax_work,
            fax_prim=self.fax_prim,
            gids=gids, gnames=None, gcid=self.gcid)

        return self.gc_entry


    def push_to_google (self):
        MAX_RETRIES = 3

        ## FIXME need to check if self.gcapi is valid

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
                                                  ph_home2=self.ph_home2,
                                                  ph_other=self.ph_other,
                                                  ph_work=self.ph_work,
                                                  ph_work2=self.ph_work2,
                                                  fax_home=self.fax_home,
                                                  fax_work=self.fax_work,
                                                  fax_prim=self.fax_prim,
                                                  )

                i = MAX_RETRIES
            except Exception, e:
                ## Should make it a bit more granular
                logging.error('Exception (%s) uploading. Will Retry (%d)',
                              e, i)

        # Now store the Google Contacts ID in Outlook, so we'll be able
        # to compare the records from the two sources at a later time.
        self.update_prop_by_name([(self.config.get_gc_guid(),
                                   self.config.get_gc_id())],
                                 mapitags.PT_UNICODE,
                                 entry.id.text)


    def verify_google_id (self):
        """Internal Test function to check if tag storage works.

        This is intended to be used for debug to retrieve and print the
        value of the Google Contacts Entry ID that is stored in MS
        Outlook.
        """

        prop_tag = self.ol.get_gid_prop_tag()

        hr, props = self.ol_item.GetProps([prop_tag], mapi.MAPI_UNICODE)
        (tag, val) = props[0]
        if mapitags.PROP_TYPE(tag) == mapitags.PT_ERROR:
            print 'Prop_Tag (0x%16x) not found. Tag: 0x%16x' % (prop_tag,
                                                                (tag % (2**64)))
        else:
            print 'Google ID found for contact. ID: ', val

    ## FIXEME: Need to implement more robust error checking.
    def append_email_prop_tags (self, fields, cf):
        """MAPI is crappy.
    
        Email addresses of the EX type do not conatain an SMTP address
        value for their PR_EMAIL_ADDRESS property tag. While the desired
        smtp address is present in the system the property tag that will
        help us fetch it is not a constant and will differ from system
        to system, and from PST file to PST file. The tag has to be
        dynamically generated.
    
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
    

def print_prop (tag, value):
    prop_type = mapitags.PROP_TYPE(tag)
    prop_id   = mapitags.PROP_ID(tag)

    if prop_type & mapitags.MV_FLAG:
        print "Tag: 0x%16x (Multi Value); Value: %s" % (long(tag), value)
    else:
        print "Tag: %s; Value: %s" % (mapiutil.GetPropTagName(tag), value)

def print_all_props (contact):
    for t, v in contact:
        print_prop(t, v)


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

    for t, v in contact:
#        t = long(t % 2**64)
        if t in fields:
            ar[t].append(v)
    
    return ar


def print_values (values):
    for k, v in values.items():
        logging.debug("Tag: 0x%16x; Value: %s",
                      long(k), v)


def main (argv=None):
    print 'Hello World'

if __name__ == "__main__":
    main()
