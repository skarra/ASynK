##
## Created : Sun Dec 04 19:42:50 IST 2011
##
## Copyright (C) 2011, 2012, 2013 Sriram Karra <karra.etc@gmail.com>
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
## This file extends the Contact base class to implement an Outlook Contact
## item while implementing the base class methods.

import string
import base64, logging, os, re, sys, traceback, utils
from   datetime import datetime

from   contact import Contact
from   win32com.mapi import mapitags as mt
import asynk_mapitags as amt
from   win32com.mapi import mapi
import demjson, iso8601, winerror, win32api, pywintypes

class OLContactError(Exception):
    pass

class OLContact(Contact):
    prop_update_t = utils.enum('PROP_REPLACE', 'PROP_APPEND')

    def __init__ (self, folder, olprops=None, eid=None, con=None,
                  con_itemid=None):
        """Constructor for OLContact. The starting properties of the contact
        can be initialized either from an existing Contact object, or from an
        Outlook item property list. It is an error to provide both.

        It is redundant to provide both olprops (array of property tuples) and
        an entryid. The entryid will override the property list.
        """

        if ((olprops and con) or (eid and con)):
            raise OLContactError(
                'Both olprops/eid and con cannot be specified in OLContact()')

        if olprops and eid:
            logging.warning('olprops and eid are not null. Ignoring olprops')
            olprops = None

        Contact.__init__(self, folder, con)

        conf = self.get_config()
        if con:
            if con_itemid:
                self.set_entryid(base64.b64decode(con_itemid))
            else:
                logging.debug('Potential new OLContact: %s', con.get_name())

        ## Set up some of the basis object attributes and parent folder/db
        ## properties to make it easier to access them

        self.set_synchable_fields_list()
        self.set_proptags(folder.get_proptags())
        pvalu = self.get_proptags().valu

        self.addr_map = {
            'work' : {
                'street'  : pvalu('ASYNK_PR_WORK_ADDRESS_STREET'),
                'city'    : pvalu('ASYNK_PR_WORK_ADDRESS_CITY'),
                'state'   : pvalu('ASYNK_PR_WORK_ADDRESS_STATE_OR_PROVINCE'),
                'country' : pvalu('ASYNK_PR_WORK_ADDRESS_COUNTRY'),
                'zip'     : pvalu('ASYNK_PR_WORK_ADDRESS_POSTAL_CODE')
            },

            'home' : {
                'street'  : mt.PR_HOME_ADDRESS_STREET_W,
                'city'    : mt.PR_HOME_ADDRESS_CITY_W,
                'state'   : mt.PR_HOME_ADDRESS_STATE_OR_PROVINCE_W,
                'country' : mt.PR_HOME_ADDRESS_COUNTRY_W,
                'zip'     : mt.PR_HOME_ADDRESS_POSTAL_CODE_W,
            },

            'other' : {
                'street'  : mt.PR_OTHER_ADDRESS_STREET_W,
                'city'    : mt.PR_OTHER_ADDRESS_CITY_W,
                'state'   : mt.PR_OTHER_ADDRESS_STATE_OR_PROVINCE_W,
                'country' : mt.PR_OTHER_ADDRESS_COUNTRY_W,
                'zip'     : mt.PR_OTHER_ADDRESS_POSTAL_CODE_W,
            },
        }

        self.set_olprops(olprops)

        if olprops:
            self.init_props_from_olprops(olprops)
        elif eid:
            self.init_props_from_eid(eid)

        self.in_init(False)

    def set_synchable_fields_list (self):
        fields = self.get_db().get_db_config()['sync_fields']
        fields = self._process_sync_fields(fields)
        ptags  = self.get_folder().get_proptags()

        fields.append(ptags.valu('ASYNK_PR_FILE_AS'))
        fields.append(ptags.valu('ASYNK_PR_EMAIL_1'))
        fields.append(ptags.valu('ASYNK_PR_EMAIL_2'))
        fields.append(ptags.valu('ASYNK_PR_EMAIL_3'))
        fields.append(ptags.valu('ASYNK_PR_IM_1'))
        fields.append(ptags.valu('ASYNK_PR_WORK_ADDRESS_POST_OFFICE_BOX'))
        fields.append(ptags.valu('ASYNK_PR_WORK_ADDRESS_STREET'))
        fields.append(ptags.valu('ASYNK_PR_WORK_ADDRESS_CITY'))
        fields.append(ptags.valu('ASYNK_PR_WORK_ADDRESS_STATE_OR_PROVINCE'))
        fields.append(ptags.valu('ASYNK_PR_WORK_ADDRESS_COUNTRY'))
        fields.append(ptags.valu('ASYNK_PR_WORK_ADDRESS_POSTAL_CODE'))
        fields.append(ptags.valu('ASYNK_PR_TASK_DUE_DATE'))
        fields.append(ptags.valu('ASYNK_PR_TASK_STATE'))
        fields.append(ptags.valu('ASYNK_PR_TASK_RECUR'))
        fields.append(ptags.valu('ASYNK_PR_TASK_COMPLETE'))
        fields.append(ptags.valu('ASYNK_PR_TASK_DATE_COMPLETED'))
        fields.append(ptags.valu('ASYNK_PR_CUSTOM_PROPS'))

        self._append_sync_proptags(fields)
        self.set_sync_fields(fields)

    def _append_sync_proptags (self, fields):
        olcf = self.get_folder()
        pts  = olcf.get_proptags()
        sts  = pts.sync_tags

        for tag, value in sts.iteritems():
            fields.append(olcf.get_proptags().valu(tag))

    ## This method is already defined in item.py, but we need to override it
    ## here to actually save just the property back to Outlook
    def update_sync_tags (self, destid, val, save=False):
        """Update the specified sync tag with given value. If the tag does not
        already exist an entry is created."""

        self._update_prop('sync_tags', destid, val)
        if save:
            return self.save_sync_tags()

        return True

    def save_sync_tags (self):
        olitem = self.get_olitem()
        olprops = []
        self._add_sync_tags_to_olprops(olprops)
        if olprops == []:
            ## this is happening because the item could not be saved for
            ## whatever reason on remote, and a sync tag was not set as a result.
            return

        try:
            hr, res = olitem.SetProps(olprops)
            olitem.SaveChanges(0)
            return True
        except Exception, e:
            logging.critical('Could not save synctags(%s) for %s (reason: %s)',
                             olprops, self.get_name(), e)
            logging.critical('Will try to continue...')
            return False

    ##
    ## First the inherited abstract methods from the base classes
    ##

    def save (self):
        """Saves the current (new) contact to Outlook so it is
        persistent. Returns the itemid for the saved entry. Returns None in
        case of an error"""

        ## FIXME: This only takes care of new insertions. In-place updates are
        ## not taken care of by this. As of this time (May 2012) this method
        ## is only invoked for new contact creations. Updates are handld
        ## differently - see folder_ol:batch_update(), so this is not a bug,
        ## just that it would be good to have a single method deal with both
        ## cases.

        fobj = self.get_folder().get_fobj()
        msg = fobj.CreateMessage(None, 0)

        if not msg:
            return None

        olprops = self.get_olprops()

        hr, res = msg.SetProps(olprops)
        if (winerror.FAILED(hr)):
            logging.critical('push_to_outlook(): unable to SetProps (code: %x)',
                             winerror.HRESULT_CODE(hr))
            return None

        msg.SaveChanges(mapi.KEEP_OPEN_READWRITE)

        # Now that we have successfully saved the record, let's fetch the
        # entryid and return it to the caller.

        hr, props  = msg.GetProps([mt.PR_ENTRYID], mapi.MAPI_UNICODE)
        (tag, val) = props[0]
        if mt.PROP_TYPE(tag) == mt.PT_ERROR:
            logging.error('save: EntryID could not be found. Weird')
            return None
        else:
            logging.debug('Successfully Wrote contact to Outlook : %-32s',
                          self.get_name())
            return self.set_entryid(val)

    ##
    ## Now onto the non-abstract methods.
    ##

    def get_entryid (self):
        try:
            return self._get_att('entryid')
        except KeyError, e:
            return None

    def set_entryid (self, eid):
        """Set the entryid, and also the itemid - which is the base64 encoded
        value of the binary entryid."""

        if not eid:
            logging.debug('Attempting to set None eid ...')
            return

        self._set_att('entryid', eid)
        self.set_itemid(base64.b64encode(eid))
        return eid

    def get_proptags (self):
        return self.proptags

    def set_proptags (self, p):
        self.proptags = p

    def get_olitem (self):
        """Returns a reference to the underlying outlook item obtained from a
        MAPI OpenMsg() call, if possible. If the contact has just been
        created, and not been saved, there would not be a olitem yet, and in
        that case a None is returned. None is also returned in case of some
        error."""

        try:
            res = self._get_att('olitem')
        except KeyError, e:
            res = None

        if res:
            return res

        eid = self.get_entryid()
        if not eid:
            logging.debug('OLContact.get_olitem: No olitem or entryid yet')
            return None

        msgstore = self.get_folder().get_msgstore()
        res = msgstore.get_obj().OpenEntry(eid, None, mapi.MAPI_BEST_ACCESS)
        if res:
            return self._set_att('olitem', res)

    def set_olitem (self, olitem):
        return self._set_att('olitem', olitem)

    def get_sync_fields (self):
        return self._get_att('sync_fields')

    def set_sync_fields (self, sf):
        return self._set_att('sync_fields', sf)

    def get_olprops (self, refresh=True):
        """Get an array of property tuples (tag, value) that is useful in MAPI
        routines. Every call to this routine will regenerate the olprops
        property array from the contacts' fields, and return it. Callers
        should cache the value if no changes are anticipated, in the interest
        of performance"""

        if refresh:
            return self.init_olprops_from_props()
        else:
            return self._get_att('olprops')

    def get_olprops_from_mapi (self, entryid=None):
        """This reads the current contact's entire property list from MAPI and
        returns an array of property tuples"""

        oli = self.get_olitem()

        # prop_list = oli.GetPropList(mapi.MAPI_UNICODE)
        # hr, props = oli.GetProps(prop_list, 0)
        # hr, props = oli.GetProps(self.get_folder().get_def_cols(), 0)

        # The idea here is to get the full property list, and then filter down
        # to the ones we are really interested in. It was getting a bit
        # confusing, as the available property list was getting filtered
        # somewhere upstream, and we were not even seeing basic stuff like
        # PR_BODY and PR_GIVEN_NAME. The following approach works for now,
        # i.e. just set the properties we are keen on.

        hr, props = oli.GetProps(self.get_sync_fields(), 0)
        # hr, props = oli.GetProps(None, 0)

        if (winerror.FAILED(hr)):
            logging.error('get_olprops_from_mapi: Unable to GetProps. Code: %x',
                          winerror.HRESULT_CODE(hr))
            logging.error('Formatted error: %s', win32api.FormatMessage(hr))

        return props

    def set_olprops (self, olprops):
        return self._set_att('olprops', olprops)

    def init_props_from_olprops (self, olprops):
        olpd = self._make_olprop_dict(olprops, self.get_sync_fields())

        ## Load up the custom properites first up, plenty of state and stuff
        ## is stored in the custom property json
        self._snarf_custom_props_from_olprops(olpd)

        self._snarf_itemid_from_olprops(olpd)
        self._snarf_names_gender_from_olprops(olpd)
        self._snarf_notes_from_olprops(olpd)
        self._snarf_emails_from_olprops(olpd)
        self._snarf_postal_from_olprops(olpd)
        self._snarf_org_details_from_olprops(olpd)
        self._snarf_phones_and_faxes_from_olprops(olpd)
        self._snarf_dates_from_olprops(olpd)
        self._snarf_websites_from_olprops(olpd)
        self._snarf_ims_from_olprops(olpd)
        self._snarf_sync_tags_from_olprops(olpd)

    def init_props_from_eid (self, eid):
        self.set_entryid(eid)
        self.set_itemid(base64.b64encode(eid))

        self.set_olitem(None)
        props = self.get_olprops_from_mapi()

        ## FIXME: Error checking needed here.
        return self.init_props_from_olprops(props)

    def init_olprops_from_props (self):
        # There are a few message properties that are sort of 'expected' to be
        # set. Most are set automatically by the store provider or the
        # transport provider. However some have to be set by the client; so,
        # let's do the honors. More on this here:
        # http://msdn.microsoft.com/en-us/library/cc839866(v=office.12).aspx
        # http://msdn.microsoft.com/en-us/library/cc839595(v=office.12).aspx

        olprops = [(mt.PR_MESSAGE_CLASS, "IPM.Contact")]

        self._add_itemid_to_olprops(olprops)
        self._add_names_gender_to_olprops(olprops)
        self._add_notes_to_olprops(olprops)
        self._add_emails_to_olprops(olprops)
        self._add_postal_to_olprops(olprops)
        self._add_org_details_to_olprops(olprops)
        self._add_phones_and_faxes_to_olprops(olprops)
        self._add_dates_to_olprops(olprops)
        self._add_websites_to_olprops(olprops)
        self._add_ims_to_olprops(olprops)
        self._add_sync_tags_to_olprops(olprops)

        self._add_custom_props_to_olprops(olprops)

        return self.set_olprops(olprops)

    ##
    ## Internal functions that are not inteded to be called from outside.
    ##

    def _snarf_itemid_from_olprops (self, olpd):
        self.set_itemid(self._get_olprop(olpd, mt.PR_ENTRYID))
        self.set_entryid(self.get_itemid())

    def _snarf_names_gender_from_olprops (self, olpd):
        ## FIXME: Are we missing snarfing any 'ASYNK_PR_FILE_AS' paramter?
        self.set_firstname(self._get_olprop(olpd, mt.PR_GIVEN_NAME))
        self.set_middlename(self._get_olprop(olpd, mt.PR_MIDDLE_NAME))
        self.set_lastname(self._get_olprop(olpd, mt.PR_SURNAME))
        self.set_name(self._get_olprop(olpd, mt.PR_DISPLAY_NAME))
        self.set_prefix(self._get_olprop(olpd, mt.PR_DISPLAY_NAME_PREFIX))
        self.set_suffix(self._get_olprop(olpd, mt.PR_GENERATION))
        self.set_nickname(self._get_olprop(olpd, mt.PR_NICKNAME))
        self.set_gender(self._get_olprop(olpd, mt.PR_GENDER))

    def _snarf_notes_from_olprops (self, olpd):
        self.add_notes(self._get_olprop(olpd, mt.PR_BODY))

    def _snarf_emails_from_olprops (self, olpd):
        ## Build an array out of the three email addresses as applicable
        email1 = self.get_proptags().valu('ASYNK_PR_EMAIL_1')
        email2 = self.get_proptags().valu('ASYNK_PR_EMAIL_2')
        email3 = self.get_proptags().valu('ASYNK_PR_EMAIL_3')

        eds = self.get_email_domains()

        self._snarf_email(olpd, email1, eds)
        self._snarf_email(olpd, email2, eds)
        self._snarf_email(olpd, email3, eds)

    def _snarf_email (self, olpd, tag, domains):
        """Fetch the email address using the specified tag, classify the
        addres into home, work or other, and file them into the appropriate
        property field.

        tag is the property tag that is to be used to look up an email
        address from the properties array. domains is the email_domains
        dictionary from the app state config file that is used to """

        addr = self._get_olprop(olpd, tag)
        if not addr:
            return

        home, work, other = utils.classify_email_addr(addr, domains)

        if home:
            self.add_email_home(addr)
        elif work:
            self.add_email_work(addr)
        elif other:
            self.add_email_other(addr)
        else:
            self.add_email_work(addr)

    ## Outlook does not have a concept of labelled addresses. There is one
    ## address each for home, work, and other. Othere databases support any
    ## number of addresses and with labels. We have to jump through some hoops
    ## to ensure we do not lose information when we go back and forth. This is
    ## what we do:
    ##
    ## - we store the first home, work, and other addresses in the contact to
    ##   the right outlook fields.
    ##
    ## - The rest of the addresses are stored away in a postals custom
    ##   property whose structure is documented in more detail in contact.py
    ## 
    ## - In addition, the labels for the "main" addresses are stored in the
    ##   addrs custom property using the labels: "_home_addr_label",
    ##   "_work_addr_label", and "_other_addr_label". When this contact is
    ##   synched to other databases, we fetch this property and populate as
    ##   required.

    def _read_addr (self, olpd, addrs, lab, tag_st, tag_city, tag_state,
                    tag_country, tag_zip):
        try:
            label = addrs[lab]
        except KeyError, e:
            logging.debug('OL Contact %s does not have %s',
                          self.get_name(), lab)
            label = 'Home'        

        if label:
            ad = {'street'  : None,
                  'city'    : None,
                  'state'   : None,
                  'country' : None,
                  'zip'     : None,}

            street = self._get_olprop(olpd, tag_st)
            city   = self._get_olprop(olpd, tag_city)
            state  = self._get_olprop(olpd, tag_state)
            countr = self._get_olprop(olpd, tag_country)
            pin    = self._get_olprop(olpd, tag_zip)

            ad.update({'street'  : street})
            ad.update({'city'    : city})
            ad.update({'state'   : state})
            ad.update({'country' : countr})
            ad.update({'zip'     : pin})

            if street or city or state or countr or pin:
                self.add_postal(label, ad)

            if lab in addrs:
                del addrs[lab]

    def _snarf_postal_from_olprops (self, olpd):
        ## Recall that only one address will be in the property dictionary,
        ## the rest are in the custom property and will be updated later -
        ## when the custom property is read and parsed

        addrs = self.get_custom('addrs')
        if not addrs:
            return

        try:
            prim_label = addrs['_prim_addr_label']
        except KeyError, e:
            logging.debug('OL Contact %s does not have _prim_addr_label',
                          self.get_disp_name())
            prim_label = 'Home'

        ## First deal with all the directly available addresses

        for cat in ['home', 'work', 'other']:
            self._read_addr(olpd, addrs, ('_%s_addr_label' % cat),
                            self.addr_map[cat]['street'],
                            self.addr_map[cat]['city'],
                            self.addr_map[cat]['state'],
                            self.addr_map[cat]['country'],
                            self.addr_map[cat]['zip'])

            ## Now deal with the remaining addresses
            if not cat in addrs:
                continue

            for label, addr in addrs[cat].iteritems():
                self.add_postal(label, addr)

        self.del_custom('addrs')            

    def _snarf_org_details_from_olprops (self, olpd):
        self.set_company( self._get_olprop(olpd, mt.PR_COMPANY_NAME))
        self.set_title(   self._get_olprop(olpd, mt.PR_TITLE))
        self.set_dept(    self._get_olprop(olpd, mt.PR_DEPARTMENT_NAME))

    def _snarf_phones_and_faxes_from_olprops (self, olpd):
        ## Outlook does not have a concept of custom labels for different
        ## phone fields, or address fields, etc. The way we handle this is to
        ## store any custom labeling (that a contact brought with it from
        ## elsewhere) in specific custom fields. Such labels will be pickedup
        ## and processed in the method that handles custom properties, and we
        ## will rewrite the labels if required at that point. Here we use some
        ## generic labels that are used by Outlook by default.

        ph = self._get_olprop(olpd, mt.PR_PRIMARY_TELEPHONE_NUMBER)
        if ph:
            self.set_phone_prim(ph)

        ph = self._get_olprop(olpd, mt.PR_MOBILE_TELEPHONE_NUMBER)
        if ph:
            self.add_phone_mob(('Mobile', ph))

        ph = self._get_olprop(olpd, mt.PR_HOME_TELEPHONE_NUMBER)
        if ph:
            self.add_phone_home(('Home', ph))
             
        ph = self._get_olprop(olpd, mt.PR_HOME2_TELEPHONE_NUMBER)
        if ph:
            self.add_phone_home(('Home2', ph))
             
        ph = self._get_olprop(olpd, mt.PR_BUSINESS_TELEPHONE_NUMBER)
        if ph:
            self.add_phone_work(('Work', ph))
             
        ph = self._get_olprop(olpd, mt.PR_BUSINESS2_TELEPHONE_NUMBER)
        if ph:
            self.add_phone_work(('Work2', ph))
             
        ph = self._get_olprop(olpd, mt.PR_OTHER_TELEPHONE_NUMBER)
        if ph:
            self.add_phone_other(('Other', ph))

        self.set_fax_prim(
            self._get_olprop(olpd, mt.PR_PRIMARY_FAX_NUMBER))

        ph = self._get_olprop(olpd, mt.PR_HOME_FAX_NUMBER)
        if ph:
            self.add_fax_home(('Home', ph))
             
        ph = self._get_olprop(olpd, mt.PR_BUSINESS_FAX_NUMBER)
        if ph:
            self.add_fax_work(('Work', ph))             

    def _snarf_dates_from_olprops (self, olpd):
        d = self._get_olprop(olpd, mt.PR_CREATION_TIME)
        if d:
            date = utils.utc_time_to_local_ts(d)
            self.set_created(iso8601.tostring(date))
        
        d = self._get_olprop(olpd, mt.PR_BIRTHDAY)
        if d:
            d = utils.utc_time_to_local_ts(d, ret_dt=True)
            date = utils.pytime_to_yyyy_mm_dd(d)
            self.set_birthday(date)

        a = self._get_olprop(olpd, mt.PR_WEDDING_ANNIVERSARY)
        if a:
            a = utils.utc_time_to_local_ts(a, ret_dt=True)
            date = utils.pytime_to_yyyy_mm_dd(a)
            self.set_anniv(date)

    def _snarf_websites_from_olprops (self, olpd):
        self.add_web_home(self._get_olprop(olpd, mt.PR_PERSONAL_HOME_PAGE))
        self.add_web_work(self._get_olprop(olpd, mt.PR_BUSINESS_HOME_PAGE))

    # def left_overs (self):
    #     self.gcid = self._get_prop(self.get_proptags().valu('ASYNK_PR_GCID'))
    #     self.last_mod  = self._get_olprop(olpd, mt.PR_LAST_MODIFICATION_TIME)

    def _snarf_ims_from_olprops (self, olpd):
        ims   = self.get_custom('ims')

        imtag = self.get_proptags().valu('ASYNK_PR_IM_1')
        imadd = self._get_olprop(olpd, imtag)

        if not imadd:
            if ims and not len(ims) == 0:
                logging.debug('ol:sifo: No IM in Outlook but custom ims : %s',
                              ims)
            return

        if not ims or len(ims) == 0:
            logging.debug('%s is a new OL entry with IM',
                          self.get_name())
            ims = {'_im_addr_label' : 'default'}

        for label, addr in ims.iteritems():
            if label == '_im_addr_label':
                label = addr
                addr  = imadd
                self.set_im_prim(label)

            self.add_im(label, addr)

        if '_im_addr_label' in ims:
            del ims['_im_addr_label']

    def _snarf_sync_tags_from_olprops (self, olpd):
        conf = self.get_config()
        sts  = self.get_folder().get_proptags().sync_tags

        for name, tag in sts.iteritems():
            valu = self._get_olprop(olpd, tag)
            if valu:
                self.update_sync_tags(name, valu)

    def _snarf_custom_props_from_olprops (self, olpd):
        tag = self.get_proptags().valu('ASYNK_PR_CUSTOM_PROPS')
        val = self._get_olprop(olpd, tag)
        if not val:
            logging.debug('con_ol:scpfo: No custom props found: %s',
                          self.get_disp_name())
            return
        
        d = demjson.decode(val)

        ## val is a json encoded property set, some of which are purely to
        ## track OL state. Process them separately, and then update the custom
        ## prop dictionary. FIXME: For now we are assuming the entire custom
        ## field are bona fide custom property.

        self.update_custom(d)

    def _get_olprop (self, olprops, key):
        if not (key in olprops.keys()):
            return None

        if olprops[key]:
            if len(olprops[key]) > 0:
                return olprops[key][0]
            else:
                return None
        else:
            return None

    def _make_olprop_dict (self, olprops, fields):
        """olprops is an array of property tuples - the sort of thing that is
        returned by GetColumns routine of MAPI, etc. This routine takes
        olprops and converts it into a dictionary with the tag as key and
        value as the, er, value - while limiting to only those tags that are
        present in the fields array"""

        ar = {}
        for field in fields:
            ar[field] = []

        for t, v in olprops:
            if t in fields:
                ar[t].append(v)

        return ar

    def _add_itemid_to_olprops (self, olprops):
        return

    def _add_names_gender_to_olprops (self, olprops):
        fatag = self.get_proptags().valu('ASYNK_PR_FILE_AS')
        n = self.get_name()
        if self.get_fileas():
            olprops.append((fatag, self.get_fileas()))
        elif n:
            ## If there is no fileas set, Let's put in some default.
            ## The default should be configurable the user: FIXME
            olprops.append((fatag, n))

        ln = self.get_lastname()
        if ln:
            olprops.append((mt.PR_SURNAME, ln))

        mn = self.get_middlename()
        if mn:
            olprops.append((mt.PR_MIDDLE_NAME, mn))

        gn = self.get_firstname()
        if gn:
            olprops.append((mt.PR_GIVEN_NAME, gn))

        if n:
            olprops.append((mt.PR_DISPLAY_NAME, n))
        else:
            n = ''
            if gn:
                n += gn
                if ln or mn:
                    n += ' '
            if mn:
                n += mn
                if ln:
                    n += ' '
            if ln:
                n += ln

            olprops.append((mt.PR_DISPLAY_NAME, n))

        pr = self.get_prefix()
        if pr:
            olprops.append((mt.PR_DISPLAY_NAME_PREFIX, pr))

        su = self.get_suffix()
        if su:
            olprops.append((mt.PR_GENERATION, su))

    def _add_notes_to_olprops (self, olprops):
        notes = self.get_notes()
        if notes and len(notes) > 0:
            olprops.append((mt.PR_BODY, notes[0]))

    def _add_emails_to_olprops (self, olprops):
        """Outlook has space only for 3 email addressess. The Gout internal
        representation as well as the representation in other PIMDBs does not
        allow us to maintain the same order on a round trip sync without a
        significant amount of additional work. In the absence of that we do a
        hack here which is to first assign all work addresses, then home
        addresses and then finally other addresses"""

        i = 0
        for email in self.get_email_home():
            i += 1
            if i > 3:
                return

            tag = self.get_proptags().valu('ASYNK_PR_EMAIL_%d' % i)
            if email:
                olprops.append((tag, email))

        for email in self.get_email_work():
            i += 1
            if i > 3:
                return

            tag = self.get_proptags().valu('ASYNK_PR_EMAIL_%d' % i)
            if email:
                olprops.append((tag, email))

        for email in self.get_email_other():
            i += 1
            if i > 3:
                return

            tag = self.get_proptags().valu('ASYNK_PR_EMAIL_%d' % i)
            if email:
                olprops.append((tag, email))

    def _add (self, olprops, tag, val):
        if val:
            olprops.append((tag, val))

    def _add_postal_to_olprops (self, olprops):
        cust = {}

        for cat in ['home', 'work', 'other']:
            cust.update({cat : {}})
            postals = self.get_postal(type=cat)
            if postals and len(postals) > 0:
                label, addr = postals[0]
                cust.update({('_%s_addr_label' % cat) : label})

                ## The first address gets written out directly into the
                ## relevant Outlook fields

                am = self.addr_map
                self._add(olprops, am[cat]['street'],  addr['street'])
                self._add(olprops, am[cat]['city'],    addr['city'])
                self._add(olprops, am[cat]['state'],   addr['state'])
                self._add(olprops, am[cat]['country'], addr['country'])
                self._add(olprops, am[cat]['zip'],     addr['zip'])
                
                ## The rest will go into the custom property dictionary which
                ## will get picked up when custom props are written out

                for label, addr in postals[1:]:
                    cust[cat].update({label : addr})

        self.add_custom('addrs', cust)

    def _add_org_details_to_olprops (self, olprops):
        name = self.get_company()
        if name:
            olprops.append((mt.PR_COMPANY_NAME, name))

        title = self.get_title()
        if title:
            olprops.append((mt.PR_TITLE, title))

        dept = self.get_dept()
        if dept:
            olprops.append((mt.PR_DEPARTMENT_NAME, dept))

    def _add_phones_and_faxes_to_olprops (self, olprops):
        ## FIXME: The labels are being ignored. This means if we get a contact
        ## from Google to Outlook and then write it back we will not retain
        ## any of the customized labels
        ph  = self.get_phone_home()
        if len(ph) >= 1:
            label, num = ph[0]
            if num:
                olprops.append((mt.PR_HOME_TELEPHONE_NUMBER, num))
        if len(ph) >= 2:
            if num:            
                label, num = ph[1]
            olprops.append((mt.PR_HOME2_TELEPHONE_NUMBER, num))
        if len(ph) >= 3:
            ## FIXME: Additional phone numbers should be put into the custom
            ## property for later use.
            logging.error('Not so silently ignoring %d Home numbers for %s',
                          len(ph)-2, self.get_disp_name())

        ph = self.get_phone_work()
        if len(ph) >= 1:
            label, num = ph[0]
            if num:
                olprops.append((mt.PR_BUSINESS_TELEPHONE_NUMBER, num))
        if len(ph) >= 2:
            label, num = ph[1]
            if num:
                olprops.append((mt.PR_BUSINESS2_TELEPHONE_NUMBER, num))
        if len(ph) >= 3:
            logging.error('Not so silently ignoring %d Work numbers for %s',
                          len(ph)-2, self.get_disp_name())

        ph = self.get_phone_mob()
        if len(ph) >= 1:
            label, num = ph[0]
            if num:
                olprops.append((mt.PR_MOBILE_TELEPHONE_NUMBER, num))
        if len(ph) >= 2:
            logging.error('Not so silently ignoring %d Mobile numbers for %s',
                          len(ph)-1, self.get_disp_name())

        ph_prim = self.get_phone_prim()
        if ph_prim:
            olprops.append((mt.PR_PRIMARY_TELEPHONE_NUMBER, ph_prim))

        ph = self.get_fax_home()
        if len(ph) >= 1:
            label, num = ph[0]
            if num:
                olprops.append((mt.PR_HOME_FAX_NUMBER, num))

        ph = self.get_fax_work()
        if len(ph) >= 1:
            label, num = ph[0]
            if num:
                olprops.append((mt.PR_BUSINESS_FAX_NUMBER, num))

        fax_prim = self.get_fax_prim()
        if fax_prim:
            olprops.append((mt.PR_PRIMARY_FAX_NUMBER, fax_prim))

    def _add_dates_to_olprops (self, olprops):
        cd = self.get_created()
        if cd:
            cd = utils.asynk_ts_parse(cd)
            olprops.append((mt.PR_CREATION_TIME, cd))

        bday = self.get_birthday()
        if bday:
            bday = utils.yyyy_mm_dd_to_pytime(bday)
            olprops.append((mt.PR_BIRTHDAY, bday))

        anniv = self.get_anniv()
        if anniv:
            anniv = utils.yyyy_mm_dd_to_pytime(anniv)
            olprops.append((mt.PR_WEDDING_ANNIVERSARY, anniv))

    def _add_websites_to_olprops (self, olprops):
        ## FIXME: What happens to additional websites?
        web = self.get_web_home()
        if web and web[0]:
            olprops.append((mt.PR_PERSONAL_HOME_PAGE, web[0]))

        web = self.get_web_work()
        if web and web[0]:
            olprops.append((mt.PR_BUSINESS_HOME_PAGE, web[0]))

    def _add_ims_to_olprops (self, olprops):
        cust = {}
        im_prim = self.get_im_prim()

        for label, addr in self.get_im().iteritems():
            if label == im_prim:
                tag = self.get_proptags().valu('ASYNK_PR_IM_1')
                if addr:
                    olprops.append((tag, addr))
                    cust.update({'_im_addr_label' : label})
                else:
                    logging.debug('Weird. Name: %s; label: %s',
                                  self.get_name(), label)
            else:
                ## The remaining IM addresses go into the custom property like
                ## we have been doing with 
                cust.update({label : addr})

        self.add_custom('ims', cust)

    def _add_sync_tags_to_olprops (self, olprops):
        conf  = self.get_config()
        mydid = self.get_folder().get_dbid()
        olps  = conf.get_db_profiles(mydid)

        for name, val in self.get_sync_tags().iteritems():
            if not val:
                continue

            pname, dbid = conf.parse_sync_label(name)

            ## FIXME: This was put in here for a reason. I think it had
            ## something to do with "reproducing" sync labels containing the
            ## ID on the local end itself. This was the easiest fix,
            ## IIRC. This clearly conflicts with the present need. We need to
            ## solve this problem - and apply it for all the DBs.

            # if dbid == mydid:
            #     continue

            if not pname in olps:
                ## This is an interesting case of a sync tag that is existing
                ## betwen two non-OL PIM DBs. i.e. we are dealing with a
                ## contact that is already being synched between BBDB and
                ## GC. So we have a sync tag that does not belong to any
                ## outlook profile, and due to the way we store sync tags in
                ## Outlook property bag, this one should properly go to the
                ## default bunch of custom props.
                self.add_custom(name, val)
                continue

            tag = self.get_proptags().valu(name)
            if val:
                olprops.append((tag, val))

    def _add_custom_props_to_olprops (self, olprops):
        ## JSON encode the entire custom property dictionary and shove it into
        ## properties array.

        tag = self.get_proptags().valu('ASYNK_PR_CUSTOM_PROPS')
        val = self.get_custom()
        if val:
            olprops.append((tag, demjson.encode(val)))
        else:
            logging.debug('con_ol:acpto: No custom props for %s while'
                          ' saving to OL...', self.get_name())

    def _process_sync_fields (self, fields):
        """Convert the string representation of the mapi property tags to
        their actual values and return as array."""

        ar = []
        for field in fields:
            try:
                v = getattr(mt, field)
                ar.append(v)
            except AttributeError, e:
                logging.error('Field %s not found', field)

        return ar

    def test_fields_in_props (self, itemid=None):
        """Check if the the properties returned by a default search
        include all the fields that the user has requested for through
        the fields.json file. This is intended to be used for
        development and debugging purposes."""

        if not itemid:
            itemid = self.get_itemid()

        props  = dict(self.get_olprops_from_mapi()) # later to try get_olprops_from_mapi
        fields = self.get_sync_fields()
        pt     = self.get_folder().get_proptags()

        logging.debug('Type of props        : %s', type(props))
        logging.debug('Num props in props   : %d', len(props))
        logging.debug('Num fields in fields : %d', len(fields))

        for field in fields:
            if not field in props.keys():
                logging.debug('Property %35s (0x%x) not in Props.',
                             pt.name(field), field)
            else:
                logging.debug('Property %35s (0x%x)     in Props.',
                              pt.name(field), field)
