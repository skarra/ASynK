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
import pimdb_cd, utils
from   caldavclientlibrary.protocol.http.util import HTTPError

import datetime, logging, md5, re, string, uuid

def l (s):
    return s.lower()

## FIXME: This method should probably be inside vCard class. But not feeling
## adventorous enough to muck with that code
def vco_find_in_group (vco, attr, group):
    if not hasattr(vco, attr):
        return None

    elems = vco.contents[attr]
    for elem in elems:
        if elem.group == group:
            return elem

    return None

class CDContact(Contact):

    GENDER     = 'X-GENDER'
    ABDATE     = 'X-ABDATE'
    ABLABEL    = 'X-ABLABEL'
    OMIT_YEAR  = 'X-APPLE-OMIT-YEAR'
    SYNC_TAG_PREFIX  = 'X-ASYNK-SYNCTAG-'

    def __init__ (self, folder, con=None, vco=None, itemid=None):
        """vco, if not None, should be a valid vCard object (i.e. the contents
        of a vCard file, for e.g. When vco is not None, itemid should also be
        not None"""

        Contact.__init__(self, folder, con)

        self.set_etag(None)
        self.set_uid(None)
        self.set_vco(vco)
        self._group_count = 0

        ## Sometimes we might be creating a contact object from a Google
        ## contact object or other entry which might have the ID in its sync
        ## tags field. if that is present, we should use it to initialize the
        ## itemid field for the current object

        conf = self.get_config()
        if con:
            try:
                pname_re = conf.get_profile_name_re()
                label    = conf.make_sync_label(pname_re, self.get_dbid())
                tag, itemid = con.get_sync_tags(label)[0]              
                self.set_itemid(itemid)
            except Exception, e:
                logging.debug('Potential new CDContact: %s', con.get_name())

        elif vco:
            self.init_props_from_vco(vco)
            assert(itemid)
            self.set_itemid(itemid)

        self.in_init(False)

        if not self.get_uid():
            self.set_uid(str(uuid.uuid1()))

    ##
    ## First the inherited abstract methods from the base classes
    ##

    def save (self, etag=None):
        """Saves the current contact on the server."""

        fo       = self.get_folder()
        vco      = self.init_vco_from_props()
        vcf_data = vco.serialize()
        success  = True

        if self.get_itemid():
            fo.put_item(self.get_itemid(), vcf_data, 'text/vcard', etag=etag)
        else:
            assert(not etag)
            fn =  fo.get_itemid()
            if fn[-1] != '/':
                fn += "/"
            fn += md5.new(vcf_data).hexdigest() + '.vcf'

            ## FIXME: Handle errors and all that good stuff.
            self.set_itemid(fn)
            try:
                fo.put_item(fn, vcf_data, 'text/vcard')
            except HTTPError, e:
                success = False

        return success

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

    def get_etag (self):
        return self._get_att('etag')

    def set_etag (self, etag):
        return self._set_att('etag', etag)

    ## The Rest...

    def init_props_from_vco (self, vco):
        self._snarf_uid_from_vco(vco)
        self._snarf_names_gender_from_vco(vco)
        self._snarf_emails_from_vco(vco)
        self._snarf_dates_from_vco(vco)
        self._snarf_sync_tags_from_vco(vco)

    def init_vco_from_props (self):
        vco = vobject.vCard()

        if self.dirty():
            self.set_updated(datetime.datetime.utcnow())

        self._add_uid_to_vco(vco)
        self._add_prodid_to_vco(vco)
        self._add_names_gender_to_vco(vco)
        self._add_emails_to_vco(vco)
        self._add_dates_to_vco(vco)
        self._add_sync_tags_to_vco(vco)

        self.dirty(False)
        return self.set_vco(vco)

    def gen_group_name (self):
        self._group_count += 1
        return 'item%d' % self._group_count

    ##
    ## The _add_* methods
    ##

    def _snarf_uid_from_vco (self, vco):
        if not vco:
            return

        if hasattr(vco, 'uid'):
            if vco.uid and vco.uid.value:
                self.set_uid(vco.uid.value)

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
        if hasattr(vco, l(self.GENDER)):
            self.set_gender(vco.contents[l(self.GENDER)][0].value)

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

        ## Last Modification Timestamp
        if hasattr(vco, 'rev') and vco.rev.value:
            dt = pimdb_cd.CDPIMDB.parse_vcard_time(vco.rev.value)
        else:
            dt = pimdb_cd.CDPIMDB.parse_vcard_time("19800101T000000Z")
            
        self.set_updated(dt)

        ## Date of Birth
        if hasattr(vco, 'bday') and vco.bday.value:
            ign = self.OMIT_YEAR in vco.bday.params.keys()
            bday = self._parse_vcard_date(vco.bday.value, ign)
                                          
            if bday:
                self.set_birthday(bday)
            else:
                logging.warning('Ignoring unrecognized birthdate (%s) for %s',
                                vco.bday.value, self.get_disp_name())

        ## Anniversary. FIXME: We are currently only processing Apple
        ## Addressbook treatment of this vCard extension.
        if hasattr(vco, l(self.ABDATE)):
            for abdate in vco.contents[l(self.ABDATE)]:
                ign = self.OMIT_YEAR in abdate.params

                group = abdate.group
                assert(group)

                label = vco_find_in_group(vco, l(self.ABLABEL), group).value

                if label == '_$!<Anniversary>!$_':
                    self.set_anniv(self._parse_vcard_date(abdate.value, ign))
                else:
                    logging.warning('Ignoring Date field %s (%s) for (%s)',
                                    label, abdate.value, self.get_disp_name())
                    

        # FIXME: Do the same for creation timestamp

    def _snarf_sync_tags_from_vco (self, vco):
        conf      = self.get_config()
        pname_re  = conf.get_profile_name_re()
        pname_re  = "^" + l(self.SYNC_TAG_PREFIX) + pname_re + "-"

        for label, val in vco.contents.iteritems():
            if re.search(pname_re, label):
                label = string.replace(label, l(self.SYNC_TAG_PREFIX), '')
                label = string.replace('asynk-' + label, '-', ':')
                self.update_sync_tags(label, val[0].value)

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
            g = vco.add(self.GENDER.lower())
            g.value = self.get_gender()

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

    def _convert_to_vcard_date (self, bd, sep=''):
        """Return a (ign_year, date_str) tuple based on the input BBDB format
        date string."""

        ignore_year = "1604"
        res = re.search('((\d\d\d\d)|-)-(\d\d)-(\d\d)', bd)

        year  = res.group(1)
        month = res.group(3)
        day   = res.group(4)

        if year == "-":
            year = ignore_year

        ign = year if year == ignore_year else None
        return ign, "%s%s%s%s%s" % (year, sep, month, sep, day)

    def _parse_vcard_date (self, vd, ign):
        """Takes a vCard date in yyyymmdd format and returns a string
        formatted in the BBDB/google contacts date format accounting for
        ignored year."""

        res = re.search('(\d\d\d\d)(\d\d)(\d\d)', vd)
        if not res:
            ## Stupid Apple Addressbook puts out dates in two different
            ## formats...
            res = re.search('(\d\d\d\d)-(\d\d)-(\d\d)', vd)

        if res:
            year  = res.group(1)
            month = res.group(2)
            day   = res.group(3)

            if ign:
                year = "-"

            return "%s-%s-%s" % (year, month, day)

        return None

    def _add_dates_to_vco (self, vco):
        ## Last Modification Timestamp
        vco.add('rev')
        vco.rev.value = pimdb_cd.CDPIMDB.get_vcard_time(self.get_updated())

        ## Birthday
        if self.get_birthday():
            ign, day = self._convert_to_vcard_date(self.get_birthday())
            d = vco.add('bday')
            d.value = day
            if ign:
                d.params = {self.OMIT_YEAR : [ign]}

        ## FIXME: Implement support for creation date, and anniversaries.
        if self.get_anniv():
            group = self.gen_group_name()
            ign, day = self._convert_to_vcard_date(self.get_anniv(),
                                                   sep="-")
            d       = vco.add(l(self.ABDATE))
            d.value = day
            d.group = group
            d.params.update({'TYPE' : ['pref']})
            if ign:
                d.params.update({self.OMIT_YEAR : [ign]})

            la       = vco.add(l(self.ABLABEL))
            la.value = '_$!<Anniversary>!$_'
            la.group = group

    def _add_sync_tags_to_vco (self, vco):
        conf     = self.get_config()
        pname_re = conf.get_profile_name_re()
        label    = conf.make_sync_label(pname_re, self.get_dbid())

        ret = ''
        i = 0
        for key, val in self.get_sync_tags().iteritems():
            # Skip any sync tag with CardDAV IDs as values.
            if re.search(label, key) or not val:
                continue

            ## Make the label more vCard friendly
            key = string.replace(key, ':', '-')
            key = string.replace(key, 'asynk-', '')
            key = l(self.SYNC_TAG_PREFIX) + key

            la = vco.add(key)
            la.value = val
