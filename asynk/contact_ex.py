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
        pass

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
        self.set_parent_folder_id(ews_con.ParentFolderId)
        self.set_itemid(ews_con.ItemId)
        self.set_changekey(ews_con.ChangeKey)

        fn = ews_con.FirstName if ews_con.FirstName else ews_con.GivenName
        ln = ews_con.LasttName if ews_con.FirstName else ews_con.Surname
        self.set_prefix(ews_con.Title)
        self.set_firstname(fn)
        self.set_lastname(ln)
        self.set_middlename(ews_con.MiddleName)
        self.set_suffix(ews_con.Suffix)
        self.set_nickname(ews_con.Nickname)
        self.set_fileas(ews_con.FileAs)
        self.add_custom('alias', ews_con.Alias)

        self.add_notes(ews_con.Notes)

        self._snarf_emails(ews_con)
        self._snarf_phones(ews_con)

        ## FIXME: This will be some of the extended property. Need to
        ## understand that a bit more
        self.set_gender(None)

    def _snarf_emails (self, ews_con):
        """Classify each email address in ews_con as home/work/other and store
        them away. Classification is done based on the domain of the address
        as set in the config file."""

        domains = self.get_email_domains()

        for email in ews_con.Emails.entries:
            addr = email.Address
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
        for phone in ews_con.Phones.entries:
            if phone.Key == 'PrimaryPhone':
                self.add_phone_prim(phone.Number)
            elif phone.Key == 'MobilePhone':
                self.add_phone_mob(('Mobile', phone.Number))
            elif phone.Key == 'HomePhone':
                self.add_phone_home(('Home', phone.Number))
            elif phone.Key == 'HomePhone2':
                self.add_phone_home(('Home2', phone.Number))
            elif phone.Key == 'BusinessPhone':
                self.add_phone_work(('Work', phone.Number))
            elif phone.Key == 'BusinessPhone2':
                self.add_phone_work(('Work2', phone.Number))
            elif phone.Key == 'OtherTelephone':
                self.add_phone_other(('Other', phone.Number))
            elif phone.Key == 'HomeFax':
                self.add_fax_home(('Home', phone.Number))
            elif phone.Key == 'BusinessFax':
                self.add_fax_work(('Work', phone.Number))
            else:
                self.add_phone_other((phone.Key, phone.Number))

    ##
    ## some additional get and set methods
    ##

    def get_changekey (self):
        return self._get_att('ck')

    def set_changekey (self, ck):
        return self._set_att('ck', ck)
