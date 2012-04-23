## 
## Created	     : Sun Dec 04 19:42:50 IST 2011
## Last Modified : Thu Mar 22 15:07:33 IST 2012
##
## Copyright 2011 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
## 

import logging

from   gc_wrapper    import get_udp_by_key
from   win32com.mapi import mapi
from   win32com.mapi import mapitags
import gdata.data
import base64

import utils
import pywintypes

def yyyy_mm_dd_to_pytime (date_str):
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    return pywintypes.Time(dt.timetuple())

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

        self.cf       = ol.get_default_contacts_folder()
        self.msgstore = ol.get_default_msgstore()

        self.PROP_REPLACE = 0
        self.PROP_APPEND  = 1

        self.gc_entry  = self.ol_item = None
        self.fields = fields

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
                entryid = None

        if entryid:
            self.entryid = entryid
            self.ol_item = self.get_ol_item()
            hr, props = self.ol_item.GetProps(self.cf.def_ctable_cols, 0)
            # FIXME: error checking needed

        ## fixme: catch error when both are None

        self.props_list = props
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

    # def populate_fields_from_props (self):
    #     self.entryid   = self._get_prop(mapitags.PR_ENTRYID)
    #     self.name      = self._get_prop(mapitags.PR_DISPLAY_NAME)
    #     self.last_mod  = self._get_prop(mapitags.PR_LAST_MODIFICATION_TIME)
    #     self.postal    = self._get_prop(mapitags.PR_POSTAL_ADDRESS)
    #     self.notes     = self._get_prop(mapitags.PR_BODY)
    #     self.company   = self._get_prop(mapitags.PR_COMPANY_NAME)
    #     self.title     = self._get_prop(mapitags.PR_TITLE)
    #     self.dept      = self._get_prop(mapitags.PR_DEPARTMENT_NAME)
    #     self.ph_prim   = self._get_prop(mapitags.PR_PRIMARY_TELEPHONE_NUMBER)
    #     self.ph_mobile = self._get_prop(mapitags.PR_MOBILE_TELEPHONE_NUMBER)
    #     self.ph_home   = self._get_prop(mapitags.PR_HOME_TELEPHONE_NUMBER)
    #     self.ph_home2  = self._get_prop(mapitags.PR_HOME2_TELEPHONE_NUMBER)
    #     self.ph_work   = self._get_prop(mapitags.PR_BUSINESS_TELEPHONE_NUMBER)
    #     self.ph_work2  = self._get_prop(mapitags.PR_BUSINESS2_TELEPHONE_NUMBER)
    #     self.ph_other  = self._get_prop(mapitags.PR_OTHER_TELEPHONE_NUMBER)
    #     self.fax_prim  = self._get_prop(mapitags.PR_PRIMARY_FAX_NUMBER)
    #     self.fax_work  = self._get_prop(mapitags.PR_BUSINESS_FAX_NUMBER)
    #     self.fax_home  = self._get_prop(mapitags.PR_HOME_FAX_NUMBER)
    #     self.gender    = self._get_prop(mapitags.PR_GENDER)
    #     self.nickname  = self._get_prop(mapitags.PR_NICKNAME)
    #     self.birthday  = self._get_prop(mapitags.PR_BIRTHDAY)
    #     self.anniv     = self._get_prop(mapitags.PR_WEDDING_ANNIVERSARY)
    #     self.web_home  = self._get_prop(mapitags.PR_PERSONAL_HOME_PAGE)
    #     self.web_work  = self._get_prop(mapitags.PR_BUSINESS_HOME_PAGE)

    #     ## Build an aray out of the three email addresses as applicable
    #     e = self._get_prop(self.cf.prop_tags.valu('GOUT_PR_EMAIL_1'))
    #     self.emails = [e] if e else None

    #     e = self._get_prop(self.cf.prop_tags.valu('GOUT_PR_EMAIL_2'))
    #     if e:
    #         if self.emails:
    #             self.emails.append(e)
    #         else:
    #             self.emails = [e]

    #     e = self._get_prop(self.cf.prop_tags.valu('GOUT_PR_EMAIL_3'))
    #     if e:
    #         if self.emails:
    #             self.emails.append(e)
    #         else:
    #             self.emails = [e]

    #     self.gcid = self._get_prop(self.cf.prop_tags.valu('GOUT_PR_GCID'))


    def create_props_list (self, ce, gcid_tag=None):
        """ce has to be an object of type ContactEntry. This routine
        forms and returns an array of tuples that can be passed to
        SetProps() of MAPI

        gcid_tag is the named property tag used to store the gcid.

        FIXME: This routine needs to be more data driven so that adding
        additional fields becomes a breeze, and editing one place will impact
        both the outlook side as well as the google side. Currently this
        routine is, in some sense, an inverse of
        gc_wrapper.py:create_contact_entry() routine...
        """

        # There are a few message properties that are sort of 'expected' to be
        # set. Most are set automatically by the store provider or the
        # transport provider. However some have to be set by the client; so,
        # let's do the honors. More on this here:
        # http://msdn.microsoft.com/en-us/library/cc839866(v=office.12).aspx
        # http://msdn.microsoft.com/en-us/library/cc839595(v=office.12).aspx

        # props = [(mapitags.PR_MESSAGE_CLASS, "IPM.Contact")]

        if gcid_tag is None:
            gcid_tag = self.cf.prop_tags.valu('GOUT_PR_GCID')

        # if ce.name:
        #     if ce.name.full_name:
        #         props.append((mapitags.PR_DISPLAY_NAME,
        #                        ce.name.full_name.text))
        #         # We need to work harder to set the File As member, without
        #         # which... the shiny new entry will look a bit odd.
        #         fileas_prop_tag = self.cf.prop_tags.valu('GOUT_PR_FILE_AS')
        #         props.append((fileas_prop_tag, ce.name.full_name.text))

        #     if ce.name.family_name:
        #         props.append((mapitags.PR_SURNAME,
        #                        ce.name.family_name.text))
        #     if ce.name.given_name:
        #         props.append((mapitags.PR_GIVEN_NAME,
        #                        ce.name.given_name.text))
        #     if ce.name.name_prefix:
        #         props.append((mapitags.PR_DISPLAY_NAME_PREFIX,
        #                        ce.name.name_prefix.text))
        #     if ce.name.name_suffix:
        #         # It is not clear where to map this. So let's leave this for
        #         # now
        #         pass

        # # Notes field
        # if ce.content and ce.content.text:
        #     props.append((mapitags.PR_BODY, ce.content.text))

        # A reference to the contact entry's ID in Google's database. Recall
        # that this ID is not constant. Everytime it is edited it changes -
        # this is Google's way of ensuring there is no crossfire across apps
        if ce.link and gcid_tag:
            gcid = utils.get_link_rel(ce.link, 'edit')
            props.append((gcid_tag, gcid))

        # # Email addresses. Need to figure out how primary email
        # # addresses are tracked in MAPI
        # if ce.email:
        #     if len(ce.email) > 0 and ce.email[0].address:
        #         props.append((self.cf.prop_tags.valu('GOUT_PR_EMAIL_1'),
        #                        ce.email[0].address))
        #     if len(ce.email) > 1 and ce.email[1].address:
        #         props.append((self.cf.prop_tags.valu('GOUT_PR_EMAIL_2'),
        #                        ce.email[1].address))
        #     if len(ce.email) > 2 and ce.email[2].address:
        #         props.append((self.cf.prop_tags.valu('GOUT_PR_EMAIL_3'),
        #                        ce.email[2].address))

        # # Postal address
        # if ce.structured_postal_address:
        #     # FIXME: Need to implement this
        #     pass

        # if ce.organization:
        #     if ce.organization.name and ce.organization.name.text:
        #         value = ce.organization.name.text
        #         props.append((mapitags.PR_COMPANY_NAME, value))
        #     if ce.organization.title and ce.organization.title.text:
        #         value = ce.organization.title.text
        #         props.append((mapitags.PR_TITLE, value))
        #     if ce.organization.department:
        #         value = ce.organization.department.text
        #         if value:
        #             props.append((mapitags.PR_DEPARTMENT_NAME, value))

        # # Phone numbers. Need to figure out how primary phone numbers
        # # are tracked in MAPI
        # if ce.phone_number:
        #     hcnt = bcnt = 0
        #     har = [mapitags.PR_HOME_TELEPHONE_NUMBER,
        #            mapitags.PR_HOME2_TELEPHONE_NUMBER]
        #     bar = [mapitags.PR_BUSINESS_TELEPHONE_NUMBER,
        #            mapitags.PR_BUSINESS2_TELEPHONE_NUMBER]

        #     for ph in ce.phone_number:
        #         # There is only space for 2 work and 2 home numbers in
        #         # Outlook ... We will just keep overwriting the second
        #         # number. FIXME: could potentially do something smarter
        #         # here
        #         if ph.rel == gdata.data.HOME_REL and ph.text:
        #             props.append((har[hcnt], ph.text))
        #             hcnt += (1 if hcnt < 1 else 0)
        #         elif ph.rel == gdata.data.WORK_REL and ph.text:
        #             props.append((bar[bcnt], ph.text))
        #             bcnt += (1 if bcnt < 1 else 0)
        #         elif ph.rel == gdata.data.OTHER_REL and ph.text:
        #             props.append((mapitags.PR_OTHER_TELEPHONE_NUMBER,
        #                           ph.text))
        #         elif ph.rel == gdata.data.MOBILE_REL and ph.text:
        #             props.append((mapitags.PR_MOBILE_TELEPHONE_NUMBER,
        #                           ph.text))

        #         if ph.primary == 'true' and ph.text:
        #             props.append((mapitags.PR_PRIMARY_TELEPHONE_NUMBER,
        #                           ph.text))

        # if ce.nickname and ce.nickname.text:
        #     props.append((mapitags.NICKNAME, ce.nickname.text))

        # if ce.gender and ce.gender.value:
        #     props.append((mapitags.PR_GENDER, ce.gender.value))

        # if ce.birthday and ce.birthday.when:
        #     d = utils.yyyy_mm_dd_to_pytime(ce.birthday.when)
        #     props.append((mapitags.PR_BIRTHDAY, d))

        # if ce.event and len(ce.event) > 0:
        #     ann = utils.get_event_rel(ce.event, 'anniversary')
        #     if ann:
        #         dt = utils.yyyy_mm_dd_to_pytime(ann.start)
        #         props.append((mapitags.PR_WEDDING_ANNIVERSARY, dt))

        # if ce.website:
        #     for site in ce.website:
        #         if site.rel == 'home-page':
        #             props.append((maptags.PR_PERSONAL_HOME_PAGE, site.href))
        #         elif site.rel == 'work':
        #             props.append((mapitags.PR_BUSINESS_HOME_PAGE, site.href))

        # return props

    # def get_ol_item (self):
    #     if self.ol_item is None:
    #         self.ol_item = self.msgstore.OpenEntry(self.entryid, None,
    #                                                MOD_FLAG)

    #     return self.ol_item

    # def set_gcapi (self, gcapi):
    #     self.gcapi = gcapi


    def update_prop (self, prop_tag, prop_val, action):
        self.ol_item = self.get_ol_item()

        try:
            hr, props = self.ol_item.GetProps([prop_tag, mapitags.PR_ACCESS,
                                            mapitags.PR_ACCESS_LEVEL],
                                           mapi.MAPI_UNICODE)
            (tag, val)        = props[0]

            if mapitags.PROP_TYPE(tag) == mapitags.PT_ERROR:
                logging.debug('update_prop(): Prop %s (0x%16x) not found',
                              self.prop_tags.name(tag), prop_tag)
                val = ''            # This could be an int. FIXME
        except Exception, e:
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


    # def _get_prop (self, prop_tag, array=False, props=None):
    #     if not props:
    #         props = self.props

    #     if not (prop_tag in props.keys()):
    #         return None

    #     if props[prop_tag]:
    #         if array:
    #             return props[prop_tag]

    #         if len(props[prop_tag]) > 0:
    #             return props[prop_tag][0]
    #         else:
    #             return None
    #     else:
    #         return None


    # ## This routine will not be required in the new scheme of things, as the
    # ## right way to implement it will be to ues the copy constructor.
    # def get_gc_entry (self):
    #     """Create and return a gdata.contacts.data.ContactEntry
    #     object from the underlying contact properties"""

    #     if self.gc_entry:
    #         return self.gc_entry

    #     gids = [self.config.get_gid()]
    #     self.gc_entry = self.gcapi.create_contact_entry(
    #         entryid=self.entryid, name=self.name,     emails=self.emails,
    #         notes=self.notes,     postal=self.postal, company=self.company,
    #         title=self.title,     dept=self.dept,     ph_prim=self.ph_prim,
    #         ph_mobile=self.ph_mobile, ph_home=self.ph_home,
    #         ph_home2=self.ph_home2, ph_other=self.ph_other,
    #         ph_work=self.ph_work, ph_work2=self.ph_work2,
    #         fax_home=self.fax_home, fax_work=self.fax_work,
    #         fax_prim=self.fax_prim,
    #         birthday=self.birthday, anniv=self.anniv,
    #         nickname=self.nickname, gender=self.gender,
    #         web_home=self.web_home, web_work=self.web_work,
    #         gids=gids, gnames=None, gcid=self.gcid)

    #     return self.gc_entry


    # def make_props_array (self, propsd):
    #     """makes a """

    # def push_to_outlook (self):
    #     """Save the current contact to Outlook, and returns the entryid of the
    #     entry."""

    #     logging.info('Saving to Outlook: %-32s ....', self.name)
    #     msg = self.ol.CreateMessage(None, 0)

    #     if not msg:
    #         return None

    #     hr, res = msg.SetProps(self.props_list)
    #     if (winerror.FAILED(hr)):
    #         logging.critical('push_to_outlook(): unable to SetProps (code: %x)',
    #                          winerror.HRESULT_CODE(hr))
    #         return None

    #     msg.SaveChanges(mapi.KEEP_OPEN_READWRITE)

    #     # Now that we have successfully saved the record, let's fetch the
    #     # entryid and return it to the caller.
    #     hr, props = msg.GetProps([mapitags.PR_ENTRYID], mapi.MAPI_UNICODE)
    #     (tag, val) = props[0]
    #     if mapitags.PROP_TYPE(tag) == mapitags.PT_ERROR:
    #         logging.error('push_to_outlook(): EntryID could not be found. Weird')
    #         return None
    #     else:
    #         return val

    # # This routine is not used anywhere these days as making batch pushes is
    # # much more efficient. This is here only for illustrative purposes now.
    # def push_to_google (self):
    #     MAX_RETRIES = 3

    #     ## FIXME need to check if self.gcapi is valid

    #     logging.info('Uploading to Google: %-32s ....', self.name)

    #     i = 0
    #     entry = None
    #     while i < MAX_RETRIES:
    #         try:
    #             i += 1
    #             entry = self.get_gc_entry()
    #             i = MAX_RETRIES
    #         except Exception, e:
    #             ## Should make it a bit more granular
    #             logging.error('Exception (%s) uploading. Will Retry (%d)',
    #                           e, i)

    #     # Now store the Google Contacts ID in Outlook, so we'll be able
    #     # to compare the records from the two sources at a later time.
    #     self.update_prop_by_name([(self.config.get_gc_guid(),
    #                                self.config.get_gc_id())],
    #                              mapitags.PT_UNICODE,
    #                              entry.id.text)


    def verify_google_id (self):
        """Internal Test function to check if tag storage works.

        This is intended to be used for debug to retrieve and print the
        value of the Google Contacts Entry ID that is stored in MS
        Outlook.
        """

        prop_tag = self.cf.prop_tags.valu('GOUT_PR_GCID')

        hr, props = self.ol_item.GetProps([prop_tag], mapi.MAPI_UNICODE)
        (tag, val) = props[0]
        if mapitags.PROP_TYPE(tag) == mapitags.PT_ERROR:
            print 'Prop_Tag (0x%16x) not found. Tag: 0x%16x' % (prop_tag,
                                                                (tag % (2**64)))
        else:
            print 'Google ID found for contact. ID: ', val

# ## FIXME: Need to implement more robust error checking. And why is this fellow
# ## a global routine? :-)
# def get_contact_details (cf, contact, fields):
#     """Get all the values as per the tag ids mentioned in the fields
#     parameter. 'Contact' is nothing but an array of (tag, value) pairs,
#     that's it.

#     Returns an hash of field => array of values for the property.
#     """
    
#     ar = {}
#     for field in fields:
#         ar[field] = []

#     for t, v in contact:
# #        t = long(t % 2**64)
#         if t in fields:
#             ar[t].append(v)
    
#     return ar
