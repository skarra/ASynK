##
## Created : Wed Apr 03 19:02:15 IST 2013
##
## Copyright (C) 2013 Sriram Karra <karra.etc@gmail.com>
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
## This file defines a wrapper class around a CardDAV contact entry. In other
## words this file wraps a vCard object.
##

## TODO: On priority we need to sync the (a) sync tags and (b) the last
## modification time stamp. These two are critical to maintain state of
## synchronization.

from   contact    import Contact
from   vobject    import vobject
import utils
import md5, uuid

## FIXME: This method should probably be inside vCard class. But not feeling
## adventorous enough to muck with that code
def vco_find_in_group (vco, attr, group):
    if not attr in vco.keys():
        return None

    elems = vco.contents[attr]
    for elem in elems:
        if elem.group and elem.group.value == group:
            return elem

    return None

class CDContact(Contact):
    def __init__ (self, folder, con=None, vco=None, itemid=None):
        """vco, if not None, should be a valid vCard object (i.e. the contents
        of a vCard file, for e.g. When vco is not None, itemid should also be
        not None"""

        Contact.__init__(self, folder, con)

        conf = self.get_config()
        if con:
            ## FIXME: Reproduce the logic from other contact_* files for this case
            pass

        self.set_vco(vco)
        if vco:
            self.init_props_from_vco(vco)
            assert(itemid)
            self.set_itemid(itemid)

        if not (con or vco):
            self.set_uid(str(uuid.uuid1()))

    ##
    ## First the inherited abstract methods from the base classes
    ##

    def save (self):
        """Saves the current contact on the server."""

        vco = self.init_vco_from_props()
        vcf_data = vco.serialize()
        print 'vcf: ', vcf_data

        fn  = md5.new(vcf_data).hexdigest() + '.vcf'
        fo  = self.get_folder()

        fo.put_item(fn, vcf_data, 'text/vcard')

    ##
    ## Now onto the non-abstract methods.
    ##

    ## First the get/set methods
    
    def get_vco (self, refresh=False):
        vco = self._get_att('vco')
        if vco and (not refresh):
            return vco

        return self.init_vco_from_props()

    def set_vco (self, vco):
        return self._set_att('vco', vco)

    def get_uid (self):
        return self._get_att('uid')

    def set_uid (self, uid):
        return self._set_att('uid', uid)

    ## The Rest...

    def init_props_from_vco (self, vco):
        self._snarf_names_gender_from_vco(vco)
        self._snarf_emails_from_vco(vco)
        self._snarf_dates_from_vco(vco)

    def init_vco_from_props (self):
        vco = vobject.vCard()

        self._add_uid_to_vco(vco)
        self._add_prodid_to_vco(vco)
        self._add_names_gender_to_vco(vco)
        self._add_emails_to_vco(vco)
        self.add_dates_to_vco(vco)

        return self.set_vco(vco)

    ##
    ## The _add_* methods
    ##

    def _snarf_names_gender_from_vco (self, vco):
        if not vco:
            return

        if vco.n and vco.n.value:
            if vco.n.value.given:
                self.set_firstname(vco.n.value.given)

            if vco.n.value.family:
                self.set_lastname(vco.n.value.family)

            if vco.n.value.additional:
                self.set_middlename(vco.n.value.additional)

            if vco.n.value.prefix:
                self.set_prefix(vco.n.value.prefix)

            if vco.n.value.suffix:
                self.set_suffix(vco.n.value.suffix)

        ## FIXME: Need to handle the formatted name when it is present. There
        ## are known cases when the formatted name is different from the
        ## Last/First - for e.g. in apple addressbook, the FN is the orgname
        ## if the user has checked the 'company' box. So I guess the right way
        ## to handle the formatted name business is to faithfully copy
        ## whatever is there.

        ## FIXME: Even with vCard 3.0, we are able to write and read a GENDER:
        ## type. So we could just get away with using all the new vCard 4.0
        ## types with vCard 3.0 too... But we'll revisit these at a later
        ## time. For now we will use X- attributes, with a FIXME note for
        ## the extended attributes that are now supported 'natively' in vCard
        ## 4.0
        if hasattr(vco, 'x-gender'):
            self.set_gender(vco.x_gender.value)

    def _snarf_emails_from_vco (self, vco):
        if not hasattr(vco, 'email'):
            return

        emails = vco.contents['email']
        for em in emails:
            em_types = em.params['TYPE'] if 'TYPE' in em.params else None
                
            ## The following code is commented out because it deals with the
            ## case when the vCard file has custom labels associated with
            ## specific email addresses. ASynK currently does not this
            ## ability. We should be moving in the direction of treating email
            ## addresses similar to Postal Addresses and Phone numbers.
            # if em.group:
            #     label = vco_find_in_group(vco, 'x-ablabel', em.group)
            #     if not label:
            #         logging.error("Could not find label name for email: %s",
            #                       em.value)
            #         self.add_email_other(em.value)
            #         continue
            #     ## We will do something here to save the label as well.
            #     self.add_email_other(em.value)

            if em_types:
                if 'pref' in em_types:
                    self.set_email_prim(em.value)

                if 'WORK' in em_types:
                    self.add_email_work(em.value)
                elif 'HOME' in em_types:
                    self.add_email_home(em.value)
                else:
                    self.add_email_other(em.value)
            else:
                self.add_email_other(em.value)

    def _snarf_dates_from_vco (self, vco):
        if not vco:
            return

        if hasattr(vco, 'rev') and vco.rev.value:
            self.set_updated(vco.rev.value)
        else:
            self.set_updated("19800101T000000Z")
            
        # FIXME: Do the same for (a) creation timestamp, (b) anniversaries (c)
        # date of birth.

    ##
    ## the _add_* methods
    ##

    def _add_uid_to_vco (self, vco):
        vco.add('uid')
        vco.uid.value = self.get_uid()

    def _add_prodid_to_vco (self, vco):
        vco.add('prodid')
        vco.prodid.value = '-//' + utils.asynk_ver_str() + '//EN'

    def _add_names_gender_to_vco (self, vco):
        vco.add('n')
        vco.n.value = vobject.vcard.Name()
        if self.get_lastname():
            vco.n.value.family = self.get_lastname()
        if self.get_firstname():
            vco.n.value.given = self.get_firstname()

        if self.get_middlename():
            vco.n.value.additional = self.get_middlename()

        if self.get_prefix():
            vco.n.value.prefix=self.get_prefix()

        if self.get_suffix():
            vco.n.value.suffix = self.get_suffix()

        if self.get_disp_name():
            vco.add('fn')
            vco.fn.value = self.get_disp_name()

        if self.get_gender():
            vco.add('x-gender')
            vco.x_gender.value = self.get_gender()

        ## FIXME: As before ensure we handle the Formatted Name, if available.

    def _add_emails_to_vco_helper (self, vco, func, typ):
        email_prim = self.get_email_prim()
        for email in func():
            if not email:
                continue

            e = vco.add('email')
            e.value = email

            if email_prim:
                e.params.update({'TYPE' : ['INTERNET', 'pref']})
            else:
                e.params.update({'TYPE' : ['INTERNET']})

            if typ:
                e.params['TYPE'].append(typ)

    def _add_emails_to_vco (self, vco):
        self._add_emails_to_vco_helper(vco, self.get_email_home, 'HOME')
        self._add_emails_to_vco_helper(vco, self.get_email_work, 'WORK')
        self._add_emails_to_vco_helper(vco, self.get_email_other, '')

    def _add_dates_to_vco (self, vco):

        ## FIXME: Implement support for creation date, DOB and anniversaries.
        vco.add('rev')
        vco.rev.value = self.get_updated()
