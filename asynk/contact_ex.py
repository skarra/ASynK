##
## Created : Wed Apr 02 11:31:26 IST 2014
##
## Copyright (C) 2014 Sriram Karra <karra.etc@gmail.com>
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
## This file extends the Contact base class to implement an Exchange Contact
## item while implementing the base class methods.
##

import logging

from   contact            import Contact
from   pyews.ews          import contact as ews_c
from   pyews.ews          import mapitags
from   pyews.ews.data     import ews_pt, ews_pid
from   pyews.ews.data     import MapiPropertyTypeType as mptt
from   pyews.ews.contact  import CompleteName as ews_cn
from   pyews.ews.contact  import Contact as EWSContact
import utils
import demjson

class EXContactError(Exception):
    pass

class EXContact(Contact):
    prop_update_t = utils.enum('PROP_REPLACE', 'PROP_APPEND')

    def __init__ (self, folder, ews_con=None, con=None, con_itemid=None):
        """Constructor for EXContact. The starting properties of the contact
        can be initialized either from an existing Contact object, or from an
        pyews contact object. It is an error to provide both.
        """

        if (ews_con and con):
            raise EXContactError(
                'Both ews con and con cannot be specified in EXContact()')

        Contact.__init__(self, folder, con)

        conf = self.get_config()
        if con:
            if con_itemid:
                self.set_itemid(con_itemid)
            else:
                logging.debug('Potential new EXContact: %s', con.get_disp_name())

        self.set_ews_con(ews_con)
        if ews_con is not None:
            self.init_props_from_ews_con(ews_con)

    ##
    ## First the inherited abstract methods from the base classes
    ##

    def save (self):
        """Saves the current contact on the server. For now we are only
        handling a new contact creation scneario. The protocol for updates is
        different"""

        logging.debug('Saving contact (%s) to server...', self.get_disp_name())
        ews_con = self.init_ews_con_from_props()
        resp = ews_con.save()
        logging.debug('Saving contact to server...done')
        # FIXME: Get the contact ID and do something meaningful with it

    ##
    ## Now onto the non-abstract methods.
    ##

    def get_parent_folder_id (self):
        """Fetch and return the itemid of the parent folder of this contact in
        the Exchange store. This will be none if this is a new contact that
        has not yet be written to the server"""

        try:
            return self._get_att('parentid')
        except Exception, e:
            return None

    def set_parent_folder_id (self, pfid):
        return self._set_att('parentid', pfid)
        
    ##
    ## And now, the internal methods
    ##

    def init_props_from_ews_con (self, ews_con):
        self._snarf_custom_props_from_ews_con(ews_con)

        self._snarf_itemid_from_ews_con(ews_con)
        self._snarf_names_gender_from_ews_con(ews_con)
        self._snarf_notes_from_ews_con(ews_con)
        self._snarf_emails_from_ews_con(ews_con)
        self._snarf_postal_from_ews_con(ews_con)
        self._snarf_org_details_from_ews_con(ews_con)
        self._snarf_phones_and_faxes_from_ews_con(ews_con)
        self._snarf_dates_from_ews_con(ews_con)
        self._snarf_websites_from_ews_con(ews_con)
        self._snarf_ims_from_ews_con(ews_con)
        self._snarf_sync_tags_from_ews_con(ews_con)

    def init_ews_con_from_props (self):
        """Return a newly populated object of type pyews.ews.contact.Contact
        with the data fields of the present contact."""

        ews = self.get_db().get_ews()
        parent_fid = self.get_folder().get_itemid()
        ews_con = EWSContact(ews, parent_fid)

        self._add_itemid_to_ews_con(ews_con)
        self._add_names_gender_to_ews_con(ews_con)
        self._add_notes_to_ews_con(ews_con)
        self._add_emails_to_ews_con(ews_con)
        self._add_postal_to_ews_con(ews_con)
        self._add_org_details_to_ews_con(ews_con)
        self._add_phones_and_faxes_to_ews_con(ews_con)
        self._add_dates_to_ews_con(ews_con)
        self._add_websites_to_ews_con(ews_con)
        self._add_ims_to_ews_con(ews_con)
        self._add_sync_tags_to_ews_con(ews_con)
        self._add_custom_props_to_ews_con(ews_con)

        return self.set_ews_con(ews_con)

    ##
    ## Internal functions that are not inteded to be called from outside.
    ##

    def _snarf_itemid_from_ews_con (self, ews_con):
        self.set_parent_folder_id(ews_con.parent_fid.value)
        self.set_itemid(ews_con.itemid.value)
        self.set_changekey(ews_con.change_key.value)

    def _snarf_names_gender_from_ews_con (self, ews_con):
        self.set_fileas(ews_con.file_as.value)
        if ews_con.alias.value is not None:
            self.add_custom('alias', ews_con.alias.value)
        self.set_name(ews_con._displayname)
        # Ignore ews_con.spouse_name
        cn = ews_con.complete_name
        fn = ews_con._firstname
        ln = ews_con._lastname
        self.set_prefix(cn.title.value)
        self.set_firstname(fn)
        self.set_lastname(ln)
        self.set_middlename(cn.middle_name.value)
        self.set_suffix(cn.suffix.value)
        self.set_nickname(cn.nickname.value)

        g = str(ews_con.gender)
        self.set_gender(None if g == 'Unspecified' else g)

    def _snarf_notes_from_ews_con (self, ews_con):
        self.add_notes(ews_con.notes.value)

    def _snarf_emails_from_ews_con (self, ews_con):
        """Classify each email address in ews_con as home/work/other and store
        them away. Classification is done based on the domain of the address
        as set in the config file."""

        domains = self.get_email_domains()

        for email in ews_con.emails.entries:
            addr = email.value
            home, work, other = utils.classify_email_addr(addr, domains)

            if home:
                self.add_email_home(addr)
            elif work:
                self.add_email_work(addr)
            elif other:
                self.add_email_other(addr)
            else:
                self.add_email_work(addr)

    def _snarf_postal_from_ews_con (self, ews_con):
        pass

    def _snarf_org_details_from_ews_con (self, ews_con):
        self.set_title(ews_con.job_title.value)
        self.set_company(ews_con.company_name.value)
        self.set_dept(ews_con.department.value)
        # Ignoring manager_name and assistant_name

    def _snarf_phones_and_faxes_from_ews_con (self, ews_con):
        ph_labels = self.get_custom('phones')
        fa_labels = self.get_custom('faxes')

        for phone in ews_con.phones.entries:
            key = phone.attrib['Key']

            if key == 'PrimaryPhone':
                self.set_phone_prim(phone.value)
            elif key == 'MobilePhone':
                if ph_labels and phone.value in ph_labels['mob']:
                    label = ph_labels['mob'][phone.value]
                else:
                    label = 'Mobile'
                self.add_phone_mob((label, phone.value))
            elif key == 'HomePhone':
                if ph_labels and phone.value in ph_labels['home']:
                    label = ph_labels['home'][phone.value]
                else:
                    label = 'Home'
                self.add_phone_home((label, phone.value))
            elif key == 'HomePhone2':
                if ph_labels and phone.value in ph_labels['home']:
                    label = ph_labels['home'][phone.value]
                else:
                    label = 'Home2'
                self.add_phone_home((label, phone.value))
            elif key == 'BusinessPhone':
                if ph_labels and phone.value in ph_labels['work']:
                    label = ph_labels['work'][phone.value]
                else:
                    label = 'Work'
                self.add_phone_work(('Work', phone.value))
            elif key == 'BusinessPhone2':
                if ph_labels and phone.value in ph_labels['work']:
                    label = ph_labels['work'][phone.value]
                else:
                    label = 'Work2'
                self.add_phone_work((label, phone.value))
            elif key == 'OtherTelephone':
                if ph_labels and phone.value in ph_labels['other']:
                    label = ph_labels['other'][phone.value]
                else:
                    label = 'Other'
                self.add_phone_other(('Other', phone.value))
            elif key == 'HomeFax':
                if fa_labels and phone.value in fa_labels['other']:
                    label = fa_labels['home'][phone.value]
                else:
                    label = 'Other'
                self.add_fax_home((label, phone.value))
            elif key == 'BusinessFax':
                if fa_labels and phone.value in fa_labels['other']:
                    label = fa_labels['work'][phone.value]
                else:
                    label = 'Other'
                self.add_fax_work((label, phone.value))
            else:
                self.add_phone_other((key, phone.value))

        self.del_custom('phones')
        self.del_custom('faxes')

    def _snarf_dates_from_ews_con (self, ews_con):
        self.set_created(ews_con.created_time.value)
        self.set_updated(ews_con.last_modified_time.value)
        self.set_birthday(ews_con.birthday.value)
        self.set_anniv(ews_con.anniversary.value)

    def _snarf_custom_props_from_ews_con (self, ews_con):
        guid = self.get_config().get_ex_guid()
        pid  = self.get_config().get_ex_cus_pid()
        cus  = ews_con.get_named_int_property(guid, int(pid))
        if cus is not None:
            self.update_custom(demjson.decode(str(cus)))

    def _snarf_websites_from_ews_con (self, ews_con):
        self.add_web_home(ews_con.personal_home_page.value)
        self.add_web_work(ews_con.business_home_page.value)

        ## If a contact has additional web addresses they would be stashed
        ## away in a custom property.
        webs = self.get_custom('webs')
        if webs is None:
            return

        for home in webs['home']:
            self.add_web_home(home)

        for work in webs['work']:
            self.add_web_work(work)

        self.del_custom('webs')

    def _snarf_ims_from_ews_con (self, ews_con):
        im_labels = self.get_custom('ims')

        for i, im in enumerate(ews_con.ims.entries):
            if im_labels and im.value in im_labels():
                label = im_labels[im.value]
            else:
                label = im.key()

            if i == 0:
                self.set_im_prim(label)

            self.add_im(label, im.value)

        self.del_custom('ims')

    def _snarf_sync_tags_from_ews_con (self, ews_con):
        conf  = self.get_config()
        guid  = conf.get_ex_guid()
        prop_name = conf.get_ex_stags_pname()

        eprop = ews_con.get_named_str_property(guid, prop_name)
        if eprop is not None:
            stags = demjson.decode(eprop.value)
            for name, val in stags.iteritems():
                self.update_sync_tags(name, val)

    def _add_itemid_to_ews_con (self, ews_con):
        itemid = self.get_itemid()
        if itemid:
            ews_con.itemid.set(itemid)

        ck = self.get_changekey()
        if ck:
            ews_con.change_key.set(ck)

    def _add_names_gender_to_ews_con (self, ews_con):
        cn = ews_con.complete_name
        cn.title.set(self.get_prefix())
        cn.first_name.set(self.get_firstname())
        cn.given_name.set(self.get_firstname())
        cn.middle_name.set(self.get_middlename())
        cn.surname.set(self.get_lastname())
        cn.last_name.set(self.get_lastname())
        cn.suffix.set(self.get_suffix())
        cn.nickname.set(self.get_nickname())

        ews_con.file_as.set(self.get_fileas())
        ews_con.alias.set(self.get_custom('alias'))

    def _add_notes_to_ews_con (self, ews_con):
        n = self.get_notes()
        if n is not None and len(n) > 0:
            ews_con.notes.value = n[0]
            ## FIXME: Need to take care of the rest like we usually do.

    def _add_emails_to_ews_con (self, ews_con):
        """
        EWS allows only for maximum of 3 email addresses across all typmes. We
        will keep three addresses
        """

        i = 0
        left = 3

        email_prim = self.get_email_prim()
        if email_prim is not None:
            ews_con.emails.add('EmailAddress1', email_prim)
            i += 1

        i = self._add_email_helper(ews_con, self.get_email_home(), left-i, i+1)
        i = self._add_email_helper(ews_con, self.get_email_work(), left-i, i+1)
        i = self._add_email_helper(ews_con, self.get_email_other(), left-i, i+1)

    def _add_email_helper (self, ews_con, emails, n, key_start):
        """From the list of emails, add at most n emails to ews_con. Return
        actual added count.

        n is the max number of emails from the list that can be added"""

        i = 0
        for email in emails:
            if i >= n:
                ## FIXME: we are effetively losing teh remaining
                ## addresses. These should be put into a custom field
                break

            ews_con.emails.add('EmailAddress%d' % (key_start+i), email)
            i += 1

        return i

    def _add_postal_to_ews_con (self, ews_con):
        pass

    def _add_org_details_to_ews_con (self, ews_con):
        ews_con.department.value = self.get_dept()
        ews_con.company_name.value = self.get_company()
        ews_con.job_title.value = self.get_title()

    def _add_phones_and_faxes_to_ews_con (self, ews_con):
        ## Any left over data will be stored to the custom property with the
        ## key 'phones'. the structure of that property will be:
        ##
        ## { 'work' : { num : label, num : label ... }
        ##   'home' : { num : label }
        ##   'other' : { num : label } }
        ##
        ## There will be another like this for faxes.

        self._add_phones_to_ews_con(ews_con)
        self._add_faxes_to_ews_con(ews_con)

    def _add_phones_to_ews_con (self, ews_con):
        cust = {'mob' : {}, 'home' : {}, 'work' : {}, 'other' : {}}

        prim = self.get_phone_prim()
        ews_con.phones.add('PrimaryPhone', prim)

        ph =  self.get_phone_mob()
        if len(ph) >= 1:
            ews_con.phones.add('MobilePhone', ph[0][1])

        for ph in self.get_phone_home():
            cust['home'].update({ph[1] : ph[0]})

        ph =  self.get_phone_home()
        if len(ph) >= 1:
            ews_con.phones.add('HomePhone', ph[0][1])
        if len(ph) >= 2:
            ews_con.phones.add('HomePhone2', ph[1][1])

        for ph in self.get_phone_home():
            cust['home'].update({ph[1] : ph[0]})

        ph =  self.get_phone_work()
        if len(ph) >= 1:
            ews_con.phones.add('BusinessPhone', ph[0][1])
        if len(ph) >= 2:
            ews_con.phones.add('BusinessPhone2', ph[1][1])

        for ph in self.get_phone_work():
            cust['work'].update({ph[1] : ph[0]})

        ph =  self.get_phone_other()
        if len(ph) >= 1:
            ews_con.phones.add('OtherTelephone', ph[0][1])

        for ph in self.get_phone_other():
            cust['other'].update({ph[1] : ph[0]})

        self.add_custom('phones', cust)

        ## FIXME: We should have a generic place in contact.py to handle these
        ## left overs for all the db types.

    def _add_faxes_to_ews_con (self, ews_con):
        cust = {'home' : {}, 'work' : {}}

        ph =  self.get_fax_home()
        if len(ph) >= 1:
            ews_con.phones.add('HomeFax', ph[0][1])

        for ph in self.get_fax_home():
            cust['home'].update({ph[1] : ph[0]})

        ph =  self.get_fax_work()
        if len(ph) >= 1:
            ews_con.phones.add('BusinessFax', ph[0][1])

        for ph in self.get_phone_work():
            cust['work'].update({ph[1] : ph[0]})

        self.add_custom('faxes', cust)

        ## FIXME: We should have a generic place in contact.py to handle these
        ## left overs for all the db types.        

    def _add_dates_to_ews_con (self, ews_con):
        ## FIXME: Need to test to ensure these values are of the proper types
        ## for EWS.
        ews_con.created_time.set(self.get_created())
        ews_con.birthday.set(self.get_birthday())
        ews_con.anniversary.set(self.get_anniv())

    def _add_websites_to_ews_con (self, ews_con):
        cus_web = {'home' : [], 'work' : []}

        web = self.get_web_home()
        if web is not None:
            if len(web) > 0:
                ews_con.add_tagged_property(tag=mapitags.PR_PERSONAL_HOME_PAGE,
                                            value=web[0])
            if len(web) > 1:
                cus_web['home'] += web[1:]

        web = self.get_web_work()
        if web is not None:
            if len(web) > 0:
                ews_con.business_home_page.value = web[0]
            if len(web) > 1:
                cus_web['work'] += web[1:]

        self.add_custom('webs', cus_web)

    def _add_ims_to_ews_con (self, ews_con):
        cust = {}
        prim = self.get_im_prim()

        i = 1
        for label, value in self.get_ims().iteritems():
            cust.update({value : label})

            if i > 3:
                continue

            ews_label = 'ImAddress%d' % i
            if prim:
                continue

            ews_con.ims.add(ews_label, value)
            i += 1

        self.add_custom('ims', cust)

    def _add_sync_tags_to_ews_con (self, ews_con):
        ## We use Named String identified extended properites to store sync
        ## tags. Note that this is different from the way we handle this stuff
        ## in the Outlook store.
        conf  = self.get_config()
        guid  = conf.get_ex_guid()
        prop_name = conf.get_ex_stags_pname()

        ## Note also that in Outlook each sync tag is a separate field. Here
        ## it is all a single json encoded dictionary.
        val = demjson.encode(self.get_sync_tags())
        ews_con.add_named_str_property(psetid=guid, pname=prop_name,
                                       ptype=mptt[mapitags.PT_UNICODE],
                                       value=val)

    def _add_custom_props_to_ews_con (self, ews_con):
        guid = self.get_config().get_ex_guid()
        pid  = self.get_config().get_ex_cus_pid()
        val = demjson.encode(self.get_custom())
        ews_con.add_named_int_property(psetid=guid, pid=pid, value=val,
                                       ptype=mptt[mapitags.PT_UNICODE])

    ##
    ## some additional get and set methods
    ##

    def get_changekey (self):
        try:
            return self._get_att('ck')
        except KeyError, e:
            return None

    def set_changekey (self, ck):
        return self._set_att('ck', ck)

    def get_ews_con (self):
        return self._get_att('ews_con')

    def set_ews_con (self, ec):
        return self._set_att('ews_con', ec)
