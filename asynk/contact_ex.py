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

from   contact    import Contact
from   pyews.ews  import contact as ews_c
from   pyews.ews.contact  import CompleteName as ews_cn
from   pyews.ews.contact import Contact as EWSContact
import utils

class EXContactError(Exception):
    pass

class EXContact(Contact):
    prop_update_t = utils.enum('PROP_REPLACE', 'PROP_APPEND')

    def __init__ (self, folder, ews_con=None, con=None):
        """Constructor for EXContact. The starting properties of the contact
        can be initialized either from an existing Contact object, or from an
        pyews contact object. It is an error to provide both.
        """

        if (ews_con and con):
            raise EXContactError(
                'Both ews con and con cannot be specified in EXContact()')

        Contact.__init__(self, folder, con)

        ## Sometimes we might be creating a contact object from a remote
        ## source which might have the Entry ID in its sync tags field. if
        ## that is present, we should use it to initialize the itemid field
        ## for the current object

        conf = self.get_config()
        if con:
            try:
                pname_re = conf.get_profile_name_re()
                label    = conf.make_sync_label(pname_re, self.get_dbid())
                tag, itemid = con.get_sync_tags(label)[0]              
                self.set_itemid(itemid)
            except Exception, e:
                logging.debug('Potential new EXContact: %s', con.get_name())

        if ews_con is not None:
            self.init_props_from_ews_con(ews_con)

    ##
    ## First the inherited abstract methods from the base classes
    ##

    def save (self):
        """Saves the current contact on the server. For now we are only
        handling a new contact creation scneario. The protocol for updates is
        different"""

        logging.debug('Creation Successful!')
        ews_con = self.init_ews_con_from_props()
        resp = ews_con.save()
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
        withthe data fields of the present contact."""

        ews = self.get_db().get_ews()
        parent_fid = self.get_folder().get_itemid()
        ews_con = EWSContact(ews, parent_fid)

        cn = ews_con.complete_name
        cn.title.value = self.get_prefix()
        cn.first_name.value = self.get_firstname()
        cn.given_name.value = self.get_firstname()
        cn.middle_name.value = self.get_middlename()
        cn.surname.value = self.get_lastname()
        cn.last_name.value = self.get_lastname()
        cn.suffix.value = self.get_suffix()
        cn.nickname.value = self.get_nickname()

        ews_con.file_as.value = self.get_fileas()
        ews_con.alias.value = self.get_custom('alias')

        n = self.get_notes()
        if n is not None and len(n) > 0:
            ews_con.notes.value = n[0]
            ## FIXME: Need to take care of the rest like we usually do.

        ews_con.department.value = self.get_dept()
        ews_con.company_name.value = self.get_company()
        ews_con.job_title.value = self.get_title()

        return ews_con

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
        for phone in ews_con.phones.entries:
            key = phone.attrib['Key']

            if key == 'PrimaryPhone':
                self.add_phone_prim(phone.value)
            elif key == 'MobilePhone':
                self.add_phone_mob(('Mobile', phone.value))
            elif key == 'HomePhone':
                self.add_phone_home(('Home', phone.value))
            elif key == 'HomePhone2':
                self.add_phone_home(('Home2', phone.value))
            elif key == 'BusinessPhone':
                self.add_phone_work(('Work', phone.value))
            elif key == 'BusinessPhone2':
                self.add_phone_work(('Work2', phone.value))
            elif key == 'OtherTelephone':
                self.add_phone_other(('Other', phone.value))
            elif key == 'HomeFax':
                self.add_fax_home(('Home', phone.value))
            elif key == 'BusinessFax':
                self.add_fax_work(('Work', phone.value))
            else:
                self.add_phone_other((key, phone.value))

    def _snarf_dates_from_ews_con (self, ews_con):
        self.set_created(ews_con.created_time.value)
        # FIXME: Need to parse Last Modified Time
        self.set_birthday(ews_con.birthday.value)
        self.set_anniv(ews_con.anniversary.value)

    def _snarf_custom_props_from_ews_con (self, ews_con):
        pass

    def _snarf_websites_from_ews_con (self, ews_con):
        pass

    def _snarf_ims_from_ews_con (self, ews_con):
        pass

    def _snarf_sync_tags_from_ews_con (self, ews_con):
        pass

    ##
    ## some additional get and set methods
    ##

    def get_changekey (self):
        return self._get_att('ck')

    def set_changekey (self, ck):
        return self._set_att('ck', ck)
