##
## Created : Tue Mar 13 14:26:01 IST 2012
##
## Copyright (C) 2012, 2013 Sriram Karra <karra.etc@gmail.com>
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
## This file defines a wrapper class around a Google Contact entry, by
## extending the Contact abstract base Contact class. Using this class one can
## create and update contact entires in google contact folders, and manipulate
## properties, etc.
##

import logging, getopt, re, string, sys, time
from datetime import datetime
import atom, iso8601
import gdata, gdata.data, gdata.contacts.data, gdata.contacts.client

import demjson, utils
from   contact    import Contact
import folder_gc

class GCContact(Contact):
    """This class extends the Contact abstract base class to wrap a Google
    Contact"""

    def __init__ (self, folder, con=None, con_itemid=None, gce=None):
        Contact.__init__(self, folder, con)

        conf = self.get_config()
        if con:
            if con_itemid:
                self.set_itemid(self.normalize_gcid(con_itemid))
            else:
                logging.debug('Potential new GCContact: %s', con.get_disp_name())

        self.set_gce(gce)
        if gce:
            self.init_props_from_gce(gce)

        self.in_init(False)

    @classmethod
    def normalize_gcid (self, itemid):
        """Replace the projection to a normalized 'thin', regardless of
        whether the original contact had a full or a base. Also make all the
        contact URIs as https://. Return value is the itemid fixed for these
        things."""

        # Workaround for a weird Google API behaviour. Certain
        # operations only succed with the 'full' projection.
        itemid = string.replace(itemid, '/base/', '/full/')

        # The /thin/ projection has a problem with updating etags and for
        # modifications... Not sure I really understand this projection
        # stuff.
        itemid = string.replace(itemid, '/thin/', '/full/')

        # Finally, since we use the entire URL as the contact's key,
        # we need to normalize the URLs. I am not sure why Google
        # can't be more consistent at its end... but this is what we
        # got.
        itemid = string.replace(itemid, 'http://', 'https://')

        return itemid

    ##
    ## First the inherited abstract methods from the base classes
    ##

    def save (self):
        """Saves the current contact on the server. For now we are only
        handling a new contact creation scneario. The protocol for updates is
        different"""

        ## FIXME: Handle the case of updating an existing contact's details.

        gce   = self.init_gce_from_props()
        entry = self.get_db().get_gdc().CreateContact(gce)

        if entry:
            logging.debug('Creation Successful!')
            logging.debug('ID for the new contact: %s', entry.id.text)
            self.set_itemid(entry.id.text)
        else:
            logging.error('Contact creation error.')
            return None

        return entry.id.text

    ##
    ## Now onto the non-abstract methods.
    ##

    def get_gce (self, refresh=False):
        gce = self._get_att('gce')
        if gce and (not refresh):
            return gce

        return self.init_gce_from_props()

    def set_gce (self, gce):
        return self._set_att('gce', gce)

    def get_etag (self):
        try:
            return self._get_att('etag')
        except Exception, e:
            return None

    def set_etag (self, etag):
        return self._set_att('etag', etag)

    def init_props_from_gce (self, gce):
        self._snarf_itemid_from_gce(gce)
        self._snarf_names_gender_from_gce(gce)
        self._snarf_notes_from_gce(gce)
        self._snarf_group_membership_from_gce(gce)
        self._snarf_emails_from_gce(gce)
        self._snarf_postal_from_gce(gce)
        self._snarf_org_details_from_gce(gce)
        self._snarf_phones_and_faxes_from_gce(gce)
        self._snarf_dates_from_gce(gce)
        self._snarf_websites_from_gce(gce)
        self._snarf_ims_from_gce(gce)
        self._snarf_sync_tags_from_gce(gce)

        self._snarf_custom_props_from_gce(gce)

        # Google entries do not have a created entry. We should just set it to
        # the current time, and take it from there.
        if not self.get_created():
            self.set_created(iso8601.tostring(time.time()))
            self.set_updated(iso8601.tostring(time.time()))
        
    def init_gce_from_props (self):
        gce = gdata.contacts.data.ContactEntry()

        self._add_itemid_to_gce(gce)
        self._add_names_gender_to_gce(gce)
        self._add_notes_to_gce(gce)
        self._add_group_membership_to_gce(gce)
        self._add_emails_to_gce(gce)
        self._add_postal_to_gce(gce)
        self._add_org_details_to_gce(gce)
        self._add_phones_and_faxes_to_gce(gce)
        self._add_dates_to_gce(gce)
        self._add_websites_to_gce(gce)
        self._add_ims_to_gce(gce)
        self._add_sync_tags_to_gce(gce)

        self._add_custom_props_to_gce(gce)

        return self.set_gce(gce)

    def __str__ (self):
        ret = ''

        props = self.get_prop_names()
        for prop in props:
            ret += '%18s: %s\n' % (prop, self._get_prop(prop))

        return ret

    def get_curr_gmail_userid (self):
        gid = self.get_folder().get_itemid()
        return self.get_gid_gmail_userid(gid)

    def get_gid_gmail_userid (self, group_uri):
        m = re.search('/groups/([^/]*)/', group_uri)
        return m.group(1) if m else None

    ##
    ## Internal functions that are not inteded to be called from outside.
    ##

    def _snarf_itemid_from_gce (self, ce):
        if ce.id:
            self.set_itemid(self.normalize_gcid(ce.id.text))

        if ce.etag:
            self.set_etag(ce.etag)

    def _snarf_names_gender_from_gce (self, ce):
        if ce.name:
            if ce.name.additional_name:
                self.set_middlename(ce.name.additional_name.text)

            if ce.name.family_name:
                self.set_lastname(ce.name.family_name.text)

            if ce.name.given_name:
                self.set_firstname(ce.name.given_name.text)

            if ce.name.full_name:
                # The FileAs property is required for Outlook. So we need to
                # keep this around. FIXME: it should really be stored as a
                # custom property on the outlook side.
                self.set_fileas(ce.name.full_name.text)

            if ce.name.name_prefix:
                self.set_prefix(ce.name.name_prefix.text)

            if ce.name.name_suffix:
                self.set_suffix(ce.name.name_suffix.text)

        if ce.nickname:
            self.set_nickname(ce.nickname.text)

        if ce.gender:
            self.set_gender(ce.gender.value)

    def _snarf_notes_from_gce (self, ce):
        if ce.content and ce.content.text:
            self.add_notes(ce.content.text)

    def _snarf_group_membership_from_gce (self, ce):
        # The group id corresponding to the current folder is ignored, the
        # rest go into custom properties
        gids = []
        if ce.group_membership_info:
            if len(ce.group_membership_info) > 0:
                for gid in ce.group_membership_info:
                    if gid.href == self.get_folder().get_itemid():
                        continue
                    gids.append(gid.href)

                if len(gids) > 0:
                    self.add_custom('gids', demjson.encode(gids))

    def _snarf_emails_from_gce (self, ce):
        """Fetch the email entries in the specified ContactEntry object and
        populate them in the internal email address strutures."""

        ## FIXME: Custom email labels are lost. It should be handled properly.
        if ce.email:
            for email in ce.email:
                if email.address:
                    if email.rel:
                        if email.rel == gdata.data.WORK_REL:
                            self.add_email_work(email.address)
                        elif email.rel == gdata.data.HOME_REL:
                            self.add_email_home(email.address)
                        elif email.rel == gdata.data.OTHER_REL:
                            self.add_email_other(email.address)
                    else:
                        self.add_email_other(email.address)

                    if email.primary:
                        self.set_email_prim(email.address)

    rel_map = {gdata.data.WORK_REL : 'Work',
               gdata.data.HOME_REL : 'Home',
               gdata.data.OTHER_REL : 'Other',}

    def _snarf_postal_from_gce (self, ce):
        self.set_postal_prim_label(None)

        if ce.structured_postal_address:
            if len(ce.structured_postal_address) > 0:
                for addr in ce.structured_postal_address:
                    if addr.label:
                        label = addr.label
                    else:
                        label = self.rel_map[addr.rel]

                    if addr.primary == 'true':
                        ## What happens if more than one is marked as primary? Hm.
                        self.set_postal_prim_label(label)

                    ad = {'street'  : None,
                          'city'    : None,
                          'state'   : None,
                          'country' : None,
                          'zip'     : None,}
                    
                    fa = addr.formatted_address
                    if fa:
                        ad.update({'formatted_address' : fa.text})

                    st = addr.street
                    if st:
                        ad.update({'street' : st.text})

                    ci = addr.city
                    if ci:
                        ad.update({'city' : ci.text})

                    st = addr.region
                    if st:
                        ad.update({'state' : st.text})

                    co = addr.country
                    if co:
                        ad.update({'country' : co.text})

                    zi = addr.postcode
                    if zi:
                        ad.update({'zip' : zi.text})

                    self.add_postal(label, ad)

    def _snarf_org_details_from_gce (self, ce):
        if ce.organization:
            if ce.organization.name and ce.organization.name.text:
                self.set_company(ce.organization.name.text)

            if ce.organization.title and ce.organization.title.text:
                self.set_title(ce.organization.title.text)

            if ce.organization.department:
                self.set_dept(ce.organization.department.text)

    def _snarf_phones_and_faxes_from_gce (self, ce):
        if ce.phone_number:
            for ph in ce.phone_number:
                if not ph.text:
                    continue

                label = ph.label
                num   = ph.text

                if label:
                    if re.search('Home', label):
                        self.add_phone_home((label, num))
                    elif re.search('(Work)|(Office)', label):
                        self.add_phone_work((label, num))
                    elif re.search('(Other)|(Misc)', label):
                        self.add_phone_other((label, num))
                    elif re.search('Mobile', label):
                        self.add_phone_mob((label, num))
    
                    elif re.search('Home Fax', label):
                        self.add_fax_home(('Home', num))
                    elif re.search('Work Fax', label):
                        self.add_fax_work(('Work', num))                    
                else:
                    if ph.rel == gdata.data.HOME_REL:
                        self.add_phone_home(('Home', num))
                    elif ph.rel == gdata.data.WORK_REL:
                        self.add_phone_work(('Work', num))
                    elif ph.rel == gdata.data.OTHER_REL:
                        self.add_phone_other(('Other', num))
                    elif ph.rel == gdata.data.MOBILE_REL:
                        self.add_phone_mob(('Mobile', num))
    
                    elif ph.rel == gdata.data.HOME_FAX_REL:
                        self.add_fax_home(('Home', num))
                    elif ph.rel == gdata.data.WORK_FAX_REL:
                        self.add_fax_work(('Work', num))

                if ph.primary == 'true':
                    if ph.rel in [gdata.data.HOME_REL, gdata.data.WORK_REL,
                                  gdata.data.OTHER_REL, gdata.data.MOBILE_REL]:
                        self.set_phone_prim(num)
                    elif ph.rel in [gdata.data.HOME_FAX_REL,
                                    gdata.data.WORK_FAX_REL]:
                        self.set_fax_prim(num)

    def _snarf_dates_from_gce (self, ce):
        if ce.birthday and ce.birthday.when:
            self.set_birthday(ce.birthday.when)

        if ce.event and len(ce.event) > 0:
            ann = utils.get_event_rel(ce.event, 'anniversary')
            if ann:
                self.set_anniv(ann.start)

    def _snarf_websites_from_gce (self, ce):
        if ce.website:
            for site in ce.website:
                if site.rel == 'home-page':
                    self.add_web_home(site.href)
                elif site.rel == 'work':
                    self.add_web_work(site.href)

    im_proto_label_map = {
        'http://schemas.google.com/g/2005#AIM'         : 'AOL',
        'http://schemas.google.com/g/2005#MSN'         : 'MSN',
        'http://schemas.google.com/g/2005#YAHOO'       : 'Yahoo',
        'http://schemas.google.com/g/2005#SKYPE'       : 'Skype',
        'http://schemas.google.com/g/2005#QQ'          :  'QQ',
        'http://schemas.google.com/g/2005#GOOGLE_TALK' : 'GTalk',
        'http://schemas.google.com/g/2005#ICQ'         : 'ICQ',
        'http://schemas.google.com/g/2005#JABBER'      : 'Jabber',
    }

    im_label_proto_map = {}
    for key, val in im_proto_label_map.iteritems():
        im_label_proto_map.update({val : key})

    def _snarf_ims_from_gce (self, ce):
        ## FIXME: The Google IMs list implementation is rather complex. There
        ## can be labels, rels, and protocols. They all appear
        ## redundant. Perhaps label will not always be set? This needs to be
        ## investigated. But this is a good start
        if ce.im:
            for im in ce.im:
                label = 'Default'         # this should never go 'on the wire'

                # The way Google uses protocol and label is a bit confusing...
                if im.label:
                    if not im.protocol:
                        im.protocol = im.label

                if im.protocol:
                    if im.protocol in self.im_proto_label_map:
                        label = self.im_proto_label_map[im.protocol]
                    else:
                        label = im.protocol
                else:
                    ## No protocol, and no label. We need to do some general
                    ## stuff here...
                    rel_re = 'http://schemas.google.com/g/2005#(.*)'
                    res = re.search(rel_re, im.rel)
                    if res:
                        label = res.group(1)
                    else:
                        label = 'Other'   # Hm, alright. I give up
                    
                self.add_im(label, im.address)
                if im.primary == 'true':
                    self.set_im_prim(label)

    def _snarf_sync_tags_from_gce (self, ce):
        if ce.user_defined_field:
            keyprefix = (self.get_config().get_label_prefix() +
                         self.get_config().get_label_separator())
            stgs = folder_gc.get_udps_by_key_prefix(
                ce.user_defined_field, keyprefix)

            self.set_sync_tags(stgs)

    def _snarf_custom_props_from_gce (self, ce):
        ## Iterate through the user_defined_propertie and do something with
        ## them...
        stag_re = (self.get_config().get_label_prefix() +
                   self.get_config().get_label_separator())
        if ce.user_defined_field:
            for ep in ce.user_defined_field:
                if ep.key == 'created':
                    self.set_created(ep.value)
                elif not re.search(stag_re, ep.key):
                    self.add_custom(ep.key, ep.value)

    def _is_valid_ph (self, phone, type):
        phone = phone.strip()
        valid = True
        if (phone == '' or phone == '-' or phone == '_'):
            valid = False

        if not valid:
            logging.info('Invalid %s number for contact %s. Skipping field',
                         type, self.get_name())

        return valid

    def _is_invalid_ph (self, phone, type):
        return (not self._is_valid_ph(phone, type))

    def _add_itemid_to_gce (self, gce):
        itemid = self.get_itemid()
        if itemid:
            gce.id = atom.data.Id(text=itemid)
        else:
            pass
            # logging.debug('Potential new contact to GC: %s',
            #               self.get_name())

        etag = self.get_etag()
        if etag:
            gce.etag = etag

    def _add_names_gender_to_gce (self, gce):
        """Populate the Name fields in gce, which is a Google ContactEntry
        object. Values for the name fields are obtained from the current
        objects property fields that should have been set earlier"""

        n = gdata.data.Name()

        text = self.get_firstname()
        if text:
            n.given_name = gdata.data.GivenName(text=text)

        text = self.get_lastname()
        if text:
            n.family_name = gdata.data.FamilyName(text=text)

        text = self.get_middlename()
        if text:
            n.additional_name = gdata.data.AdditionalName(text=text)

        text = self.get_name()
        if text:
            n.full_name = gdata.data.FullName(text=text)

        text = self.get_suffix()
        if text:
            n.name_suffix = gdata.data.NameSuffix(text=text)

        text = self.get_prefix()
        if text:
            n.name_prefix = gdata.data.NamePrefix(text=text)

        gce.name = n

        text = self.get_nickname()
        if text:
            gce.nickname = gdata.contacts.data.NickName(text=text)

        text = self.get_gender()
        if text:
            gce.gender = gdata.contacts.data.Gender(value=text)


    def _add_notes_to_gce (self, gce):
        """Append the Notes field to the specified ContactEntry object. As of
        now only the first Notes entry is copied. In future the remaining
        ones will be mapped into the custom fields section."""

        ## FIXME: Google allows only a single notes field, Others, like BBDB,
        ## can have multiple. For now just deal with the first entry and
        ## ignore the rest. Eventually we could put these things in custom
        ## fields...

        notes = self.get_notes()
        if notes:
            gce.content = atom.data.Content(text=notes[0])

    def _add_group_membership_to_gce (self, gce):
        """Append the group IDs that denote group membership to the specified
        ContactEntry object."""

        gmail_owner = self.get_curr_gmail_userid()

        gid = self.get_folder().get_itemid()
        gidm = gdata.contacts.data.GroupMembershipInfo(href=gid)
        gce.group_membership_info.append(gidm)

        if not self.get_custom('gids'):
            return

        js = self.get_custom('gids')
        js = js.replace('\\', '')
        gids = demjson.decode(js)

        retained_gids = []
        for gid in gids:
            gid_owner = self.get_gid_gmail_userid(gid)
            if gid_owner == gmail_owner:
                gidm = gdata.contacts.data.GroupMembershipInfo(href=gid)
                gce.group_membership_info.append(gidm)
            else:
                logging.debug(('Skipped mismatched membership in gid: %s; ' +
                              'Current Owner: %s'), gid, gmail_owner)
                retained_gids.append(gid)

        self.update_custom({'gids' : demjson.encode(retained_gids)})

    def _add_emails_to_gce (self, gce):
        """Append the email addresses from the current Contact object to the
        specified ContactEntry object."""

        email_prim = self.get_email_prim()

        for email in self.get_email_home():
            if not email:
                continue
            prim = 'true' if email == email_prim else 'false'
            em = gdata.data.Email(address=email, primary=prim,
                                  rel=gdata.data.HOME_REL)
            gce.email.append(em)

        for email in self.get_email_work():
            if not email:
                continue
            prim = 'true' if email == email_prim else 'false'
            em = gdata.data.Email(address=email, primary=prim,
                                  rel=gdata.data.WORK_REL)
            gce.email.append(em)

        for email in self.get_email_other():
            if not email:
                continue
            prim = 'true' if email == email_prim else 'false'
            em = gdata.data.Email(address=email, primary=prim,
                                  rel=gdata.data.OTHER_REL)
            gce.email.append(em)


    def _add_postal_to_gce (self, gce):
        """Insert the address fields from current contact object into the
        ContactEntry object."""

        postals = self.get_postal(as_array=True)
        for label, postal in postals:
            if postal:
                prim = 'true' if self.is_postal_prim(label) else 'false'
                add  = gdata.data.StructuredPostalAddress(
                    label=label, primary=prim)

                if postal['street']:
                    strt = gdata.data.Street(text=postal['street'])
                    add.street = strt

                if postal['city']:
                    city = gdata.data.City(text=postal['city'])
                    add.city = city

                if postal['state']:
                    state = gdata.data.Region(text=postal['state'])
                    add.region = state

                if postal['country']:
                    country = gdata.data.Country(text=postal['country'])
                    add.country = country

                if postal['zip']:
                    postcode = gdata.data.Postcode(text=postal['zip'])
                    add.postcode = postcode

                k = 'formatted_address'
                fa = postal[k] if k in postal else None
                if fa:
                    fad = gdata.data.FormattedAddress(text=fa)
                    add.formatted_address = fad

                gce.structured_postal_address.append(add)

    def _add_org_details_to_gce (self, gce):
        """Insert the contact's company, department and other such
        organization details into the specified ContactEntry."""

        company = self.get_company()
        title   = self.get_title()
        dept    = self.get_dept()

        on = gdata.data.OrgName(text=company)    if company else None
        ot = gdata.data.OrgTitle(text=title)     if title   else None
        od = gdata.data.OrgDepartment(text=dept) if dept    else None

        org = gdata.data.Organization(primary='true', name=on, title=ot,
                                      department=od, rel=gdata.data.WORK_REL)
        gce.organization = org


    def _add_phones_and_faxes_to_gce (self, gce):
        """Append the contact's phone details into the specified ContactEntr
        object."""

        ph_prim = self.get_phone_prim()

        for label, ph in self.get_phone_home():
            if not ph or self._is_invalid_ph(ph, 'Home'):
                continue
            prim = 'true' if ph == ph_prim else 'false'
            phone = gdata.data.PhoneNumber(text=ph, primary=prim,
                                           label=label)
            gce.phone_number.append(phone)

        for label, ph in self.get_phone_work():
            if not ph or self._is_invalid_ph(ph, 'Work'):
                continue
            prim = 'true' if ph == ph_prim else 'false'
            phone = gdata.data.PhoneNumber(text=ph, primary=prim,
                                           label=label)
            gce.phone_number.append(phone)

        for label, ph in self.get_phone_other():
            if not ph or self._is_invalid_ph(ph, 'Other'):
                continue
            prim = 'true' if ph == ph_prim else 'false'
            phone = gdata.data.PhoneNumber(text=ph, primary=prim,
                                           label=label)
            gce.phone_number.append(phone)

        for label, ph in self.get_phone_mob():
            if not ph or self._is_invalid_ph(ph, 'Mobile'):
                continue
            prim = 'true' if ph == ph_prim else 'false'
            phone = gdata.data.PhoneNumber(text=ph, primary=prim,
                                           label=label)
            gce.phone_number.append(phone)

        fax_prim = self.get_fax_prim()

        for label, fa in self.get_fax_home():
            if not fa or self._is_invalid_ph(fa, 'Home Fax'):
                continue
            prim = 'true' if fa == fax_prim else 'false'
            fax  = gdata.data.PhoneNumber(text=fa, primary=prim,
                                           label=label)
            gce.phone_number.append(fax)

        for label, fa in self.get_fax_work():
            if not fa or self._is_invalid_ph(fa, 'Work Fax'):
                continue
            prim = 'true' if fa == fax_prim else 'false'
            fax  = gdata.data.PhoneNumber(text=fa, primary=prim,
                                           label=label)
            gce.phone_number.append(fax)

    def _add_dates_to_gce (self, gce):
        """Append the date entries such as birthday and anniversary to the
        specified ContactEntry"""

        dt = self.get_birthday()
        if dt:
            gce.birthday = gdata.contacts.data.Birthday(when=dt)

        dt = self.get_anniv()
        if dt:
            date = gdata.data.When(start=dt)
            ann  = gdata.contacts.data.Event(when=date, rel='anniversary')
            gce.event.append(ann)

    def _add_websites_to_gce (self, gce):
        """Append any Web URLs from the current contact to the specified
        ContatEntry object."""

        web_prim = self.get_web_prim()

        for web in self.get_web_home():
            if not web:
                continue
            prim = 'true' if web == web_prim else 'false'
            home = gdata.contacts.data.Website(href=web, primary=prim,
                                               rel='home-page')
            gce.website.append(home)

        for web in self.get_web_work():
            if not web:
                continue
            prim = 'true' if web == web_prim else 'false'
            work = gdata.contacts.data.Website(href=web, primary=prim,
                                               rel='work')
            gce.website.append(work)

    def _add_ims_to_gce (self, gce):
        im_prim = self.get_im_prim()
        for label, addr in self.get_im().iteritems():
            prim  = 'true' if im_prim == label else 'false'
            rel   = 'http://schemas.google.com/g/2005#other'
            proto = None

            if label in self.im_label_proto_map:
                proto = self.im_label_proto_map[label]
            else:
                proto = label

            im = gdata.data.Im(protocol=proto, rel=rel,
                               address=addr, primary=prim)
            gce.im.append(im)

    def _add_sync_tags_to_gce (self, gce):
        conf     = self.get_config()
        pname_re = conf.get_profile_name_re()
        label    = conf.make_sync_label(pname_re, self.get_dbid())

        ## These will be stored as extended properties. Note that if this
        ## routine keeps appending the sync_tags to the user_defined_fields,
        ## with no regard for whether it already exists or not...
        for key, val in self.get_sync_tags().iteritems():
            ## FIXME: This was put in here for a reason. I think it had
            ## something to do with "reproducing" sync labels containing the
            ## ID on the local end itself. This was the easiest fix,
            ## IIRC. This clearly conflicts with the present need. We need to
            ## solve this problem - and apply it for all the DBs.

            # # Skip any sync tag with GCIDs as values.
            # if re.search(label, key):
            #     continue

            ud       = gdata.contacts.data.UserDefinedField()
            ud.key   = key
            ud.value = val
            gce.user_defined_field.append(ud)

    def _add_custom_props_to_gce (self, gce):
        c = self.get_created()
        if c:
            ud       = gdata.contacts.data.UserDefinedField()
            ud.key   = 'created'
            ud.value = c.isoformat() if isinstance(c, datetime) else c
            gce.user_defined_field.append(ud)

        for key, val in self.get_custom().iteritems():
            # We skip certain keys that have been processed already and
            # populated into other elements of the contact entry.
            if val and not key in []:
                ud       = gdata.contacts.data.UserDefinedField()
                ud.key   = key
                val = val.isoformat() if isinstance(val, datetime) else val
                ud.value = val
                gce.user_defined_field.append(ud)
                
    ##
    ## Temporarily placing keeping this stuff here while we start by cleaning
    ## up pimdb_gc.py
    ##

    # ## We will delete this guy very soon.

    # def add_olid_to_ce (self, ce, olid, replace=True):
    #     """Insert the Outlook EntryID for a contact as a  userdefined property
    #     in the Google ContactEntry and returned the modified ContactEntry.

    #     olid is the values as returned by GetProps - and, as a result a binary
    #     value. We base64 encode it before inserting into ContactEntry.

    #     If replace is True, then the first existing olid entry (if any) will
    #     be replaced with teh provided value. If it is False, then it is
    #     appended to existing list."""

    #     entryid_b64 = base64.b64encode(olid)
    #     ud       = gdata.contacts.data.UserDefinedField()
    #     ud.key   = 'olid'
    #     ud.value = entryid_b64

    #     if replace and len(ce.user_defined_field) > 0:
    #         ce.user_defined_field.pop()

    #     ce.user_defined_field.append(ud)

    #     return ce
