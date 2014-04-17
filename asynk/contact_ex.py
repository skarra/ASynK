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
            self._init_props_from_ews_con(ews_con)

    ##
    ## First the inherited abstract methods from the base classes
    ##

    def save (self):
        """Saves the current contact on the server. For now we are only
        handling a new contact creation scneario. The protocol for updates is
        different"""

        ews_con = self._init_ews_con_from_props(ews_con)
        ews_con.save()

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

    def _init_props_from_ews_con (self, ews_con):
        ## ItemID and related identification information

        self.set_parent_folder_id(ews_con.parent_fid.text)
        self.set_itemid(ews_con.itemid.text)
        self.set_changekey(ews_con.change_key.text)

        ## Name / Complete Name related fields

        self.set_fileas(ews_con.file_as.text)
        if ews_con.alias.text is not None:
            self.add_custom('alias', ews_con.alias.text)
        self.set_name(ews_con._displayname)
        # Ignore ews_con.spouse_name
        cn = ews_con.complete_name
        fn = ews_con._firstname
        ln = ews_con._lastname
        self.set_prefix(cn.title.text)
        self.set_firstname(fn)
        self.set_lastname(ln)
        self.set_middlename(cn.middle_name.text)
        self.set_suffix(cn.suffix.text)
        self.set_nickname(cn.nickname.text)
        # Skipping gender

        ## Notes and related fields

        self.add_notes(ews_con.notes.text)

        ## Emails

        self._snarf_emails(ews_con)

        ## Postal Addresses

        ## Org Details

        self.set_title(ews_con.job_title.text)
        self.set_company(ews_con.company_name.text)
        self.set_dept(ews_con.department.text)
        # Ignoring manager_name and assistant_name

        ## Phones and faxes

        self._snarf_phones(ews_con)

        ## Dates & Anniversaries

        self.set_created(ews_con.created_time.text)
        # Need to parse Last Modified Time
        self.set_birthday(ews_con.birthday.text)
        self.set_anniv(ews_con.anniversary.text)

        ## Websites

        ## IM Addresses

        ## Sync Tags

    def _snarf_emails (self, ews_con):
        """Classify each email address in ews_con as home/work/other and store
        them away. Classification is done based on the domain of the address
        as set in the config file."""

        domains = self.get_email_domains()

        for email in ews_con.emails.entries:
            addr = email.text
            home, work, other = utils.classify_email_addr(addr, domains)

            if home:
                self.add_email_home(addr)
            elif work:
                self.add_email_work(addr)
            elif other:
                self.add_email_other(addr)
            else:
                self.add_email_work(addr)

    def _snarf_phones (self, ews_con):
        for phone in ews_con.phones.entries:
            key = phone.attrib['Key']

            if key == 'PrimaryPhone':
                self.add_phone_prim(phone.text)
            elif key == 'MobilePhone':
                self.add_phone_mob(('Mobile', phone.text))
            elif key == 'HomePhone':
                self.add_phone_home(('Home', phone.text))
            elif key == 'HomePhone2':
                self.add_phone_home(('Home2', phone.text))
            elif key == 'BusinessPhone':
                self.add_phone_work(('Work', phone.text))
            elif key == 'BusinessPhone2':
                self.add_phone_work(('Work2', phone.text))
            elif key == 'OtherTelephone':
                self.add_phone_other(('Other', phone.text))
            elif key == 'HomeFax':
                self.add_fax_home(('Home', phone.text))
            elif key == 'BusinessFax':
                self.add_fax_work(('Work', phone.text))
            else:
                self.add_phone_other((key, phone.text))

    ##
    ## Fetch ews_con from EXContact
    ##

    def _init_ews_con_from_props (self):
        """Return a newly populated object of type pyews.ews.contact.Contact
        withthe data fields of the present contact."""

        ews = self.get_db().get_service()
        parent_fid = self.get_folder().get_itemid()
        ews_con = EWSContact(ews, parent_fid)

        ews_con.first_name = ews_c.FirstName(self.get_firsname())
        ews_con.given_name = ews_c.GivenName(self.get_firsname())
        ews_con.surname = ews_c.Surname(self.get_lastname())
        ews_con.last_name = ews_c.LastName(self.get_lastname())
        ews_con.middle_name = ews_c.MiddleName(self.get_middlename())
        ews_con.suffix = ews_c.Suffix(self.get_suffix())
        ews_con.nickname = ews_c.Nickname(self.get_nickname())
        ews_con.file_as = ews_c.FileAs(self.get_fileas())
        ews_con.alias = ews_c.Alias(self.get_custom('alias'))
        ews_con.notes = ews_c.Notes(self.get_notes()[0])

        return ews_con

    ##
    ## some additional get and set methods
    ##

    def get_changekey (self):
        return self._get_att('ck')

    def set_changekey (self, ck):
        return self._set_att('ck', ck)
