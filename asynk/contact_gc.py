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
## extending the Contact abstract base Contact class.  Uses the People API
## v1 Person resource (a plain dict) instead of the old GData ContactEntry.
##

import logging, re, time
from datetime import datetime

import demjson3 as demjson, utils
from contact import Contact
import folder_gc

## ---------------------------------------------------------------------------
## People API type constants
## ---------------------------------------------------------------------------

## Canonical type values used by the People API for emails, phones, etc.
TYPE_HOME   = 'home'
TYPE_WORK   = 'work'
TYPE_OTHER  = 'other'
TYPE_MOBILE = 'mobile'
TYPE_HOME_FAX = 'homeFax'
TYPE_WORK_FAX = 'workFax'

## IM protocol mapping between People API and ASynK labels
IM_PROTO_LABEL = {
    'aim'        : 'AOL',
    'msn'        : 'MSN',
    'yahoo'      : 'Yahoo',
    'skype'      : 'Skype',
    'qq'         : 'QQ',
    'googleTalk' : 'GTalk',
    'icq'        : 'ICQ',
    'jabber'     : 'Jabber',
}

IM_LABEL_PROTO = {v: k for k, v in IM_PROTO_LABEL.items()}

## ---------------------------------------------------------------------------
## GCContact
## ---------------------------------------------------------------------------

class GCContact(Contact):
    """This class extends the Contact abstract base class to wrap a Google
    Contact using a People API Person resource (a plain dict)."""

    def __init__ (self, folder, con=None, con_itemid=None, person=None):
        Contact.__init__(self, folder, con)

        conf = self.get_config()
        if con:
            if con_itemid:
                self.set_itemid(self.normalize_gcid(con_itemid))
            else:
                logging.debug('Potential new GCContact: %s', con.get_disp_name())

        self.set_person(person)
        if person:
            self.init_props_from_person(person)

        self.in_init(False)

    @classmethod
    def normalize_gcid (cls, itemid):
        """Normalize a Google contact ID.  For the People API, resource names
        are in the form 'people/cXXX'.  For legacy GData IDs, we normalize
        projection and scheme."""

        if itemid.startswith('people/'):
            return itemid

        # Legacy GData URL normalization (for migration)
        itemid = itemid.replace('/base/', '/full/')
        itemid = itemid.replace('/thin/', '/full/')
        itemid = itemid.replace('http://', 'https://')

        return itemid

    ##
    ## First the inherited abstract methods from the base classes
    ##

    def save (self):
        """Saves the current contact on the server."""

        person = self.init_person_from_props()
        svc = self.get_db().get_service()
        result = svc.people().createContact(
            body=person,
            personFields='names,metadata').execute()

        if result:
            rid = result.get('resourceName', '')
            logging.debug('Creation Successful!')
            logging.debug('ID for the new contact: %s', rid)
            self.set_itemid(rid)
        else:
            logging.error('Contact creation error.')
            return None

        return rid

    ##
    ## Now onto the non-abstract methods.
    ##

    def get_person (self):
        person = self._get_att('person')
        if person:
            return person
        return self.init_person_from_props()

    def set_person (self, person):
        return self._set_att('person', person)

    def get_etag (self):
        try:
            return self._get_att('etag')
        except Exception:
            return None

    def set_etag (self, etag):
        return self._set_att('etag', etag)

    ## For compatibility with folder_gc which may call get_gce/set_gce
    def get_gce (self, refresh=False):
        return self.get_person()

    def set_gce (self, val):
        return self.set_person(val)

    def init_props_from_person (self, person):
        """Parse a People API Person resource dict and populate the
        Contact properties."""

        self._snarf_itemid_from_person(person)
        self._snarf_names_gender_from_person(person)
        self._snarf_notes_from_person(person)
        self._snarf_group_membership_from_person(person)
        self._snarf_emails_from_person(person)
        self._snarf_postal_from_person(person)
        self._snarf_org_details_from_person(person)
        self._snarf_phones_and_faxes_from_person(person)
        self._snarf_dates_from_person(person)
        self._snarf_websites_from_person(person)
        self._snarf_ims_from_person(person)
        self._snarf_sync_tags_from_person(person)
        self._snarf_custom_props_from_person(person)

        # Google entries do not have a created entry. Set to now if missing.
        if not self.get_created():
            now = datetime.utcnow().isoformat() + 'Z'
            self.set_created(now)
            self.set_updated(now)

    def init_person_from_props (self):
        """Build a People API Person resource dict from the current
        Contact properties."""

        person = {}

        self._add_names_gender_to_person(person)
        self._add_notes_to_person(person)
        self._add_group_membership_to_person(person)
        self._add_emails_to_person(person)
        self._add_postal_to_person(person)
        self._add_org_details_to_person(person)
        self._add_phones_and_faxes_to_person(person)
        self._add_dates_to_person(person)
        self._add_websites_to_person(person)
        self._add_ims_to_person(person)
        self._add_sync_tags_to_person(person)
        self._add_custom_props_to_person(person)

        self.set_person(person)
        return person

    def __str__ (self):
        ret = ''
        props = self.get_prop_names()
        for prop in props:
            ret += '%18s: %s\n' % (prop, self._get_prop(prop))
        return ret

    ##
    ## Internal functions — snarf (Person → Contact props)
    ##

    def _snarf_itemid_from_person (self, person):
        rid = person.get('resourceName')
        if rid:
            self.set_itemid(self.normalize_gcid(rid))

        etag = person.get('etag')
        if etag:
            self.set_etag(etag)

    def _snarf_names_gender_from_person (self, person):
        names = person.get('names', [])
        if names:
            n = names[0]
            if n.get('middleName'):
                self.set_middlename(n['middleName'])
            if n.get('familyName'):
                self.set_lastname(n['familyName'])
            if n.get('givenName'):
                self.set_firstname(n['givenName'])
            if n.get('displayName'):
                self.set_fileas(n['displayName'])
            if n.get('honorificPrefix'):
                self.set_prefix(n['honorificPrefix'])
            if n.get('honorificSuffix'):
                self.set_suffix(n['honorificSuffix'])

        nicknames = person.get('nicknames', [])
        if nicknames:
            self.set_nickname(nicknames[0].get('value', ''))

        genders = person.get('genders', [])
        if genders:
            self.set_gender(genders[0].get('value', ''))

    def _snarf_notes_from_person (self, person):
        bios = person.get('biographies', [])
        if bios:
            text = bios[0].get('value', '')
            if text:
                self.add_notes(text)

    def _snarf_group_membership_from_person (self, person):
        memberships = person.get('memberships', [])
        folder_gid = self.get_folder().get_itemid()
        gids = []

        for m in memberships:
            cgm = m.get('contactGroupMembership', {})
            rn = cgm.get('contactGroupResourceName', '')
            if rn and rn != folder_gid:
                gids.append(rn)

        if gids:
            self.add_custom('gids', demjson.encode(gids))

    def _snarf_emails_from_person (self, person):
        for email in person.get('emailAddresses', []):
            addr = email.get('value', '')
            if not addr:
                continue

            etype = (email.get('type') or TYPE_OTHER).lower()
            if etype == TYPE_WORK:
                self.add_email_work(addr)
            elif etype == TYPE_HOME:
                self.add_email_home(addr)
            else:
                self.add_email_other(addr)

            metadata = email.get('metadata', {})
            if metadata.get('primary'):
                self.set_email_prim(addr)

    def _snarf_postal_from_person (self, person):
        self.set_postal_prim_label(None)

        for addr in person.get('addresses', []):
            atype = (addr.get('type') or TYPE_OTHER).capitalize()

            metadata = addr.get('metadata', {})
            if metadata.get('primary'):
                self.set_postal_prim_label(atype)

            ad = {
                'street'  : addr.get('streetAddress'),
                'city'    : addr.get('city'),
                'state'   : addr.get('region'),
                'country' : addr.get('country'),
                'zip'     : addr.get('postalCode'),
            }

            fa = addr.get('formattedValue')
            if fa:
                ad['formatted_address'] = fa

            self.add_postal(atype, ad)

    def _snarf_org_details_from_person (self, person):
        orgs = person.get('organizations', [])
        if orgs:
            org = orgs[0]
            if org.get('name'):
                self.set_company(org['name'])
            if org.get('title'):
                self.set_title(org['title'])
            if org.get('department'):
                self.set_dept(org['department'])

    def _snarf_phones_and_faxes_from_person (self, person):
        for ph in person.get('phoneNumbers', []):
            num = ph.get('value', '')
            if not num:
                continue

            ptype = (ph.get('type') or TYPE_OTHER).lower()

            if ptype == TYPE_HOME:
                self.add_phone_home(('Home', num))
            elif ptype == TYPE_WORK:
                self.add_phone_work(('Work', num))
            elif ptype == TYPE_MOBILE:
                self.add_phone_mob(('Mobile', num))
            elif ptype == TYPE_HOME_FAX.lower():
                self.add_fax_home(('Home', num))
            elif ptype == TYPE_WORK_FAX.lower():
                self.add_fax_work(('Work', num))
            else:
                self.add_phone_other(('Other', num))

            metadata = ph.get('metadata', {})
            if metadata.get('primary'):
                if ptype in [TYPE_HOME_FAX.lower(), TYPE_WORK_FAX.lower()]:
                    self.set_fax_prim(num)
                else:
                    self.set_phone_prim(num)

    def _snarf_dates_from_person (self, person):
        bdays = person.get('birthdays', [])
        if bdays:
            d = bdays[0].get('date', {})
            if d:
                # People API returns {year, month, day}
                parts = []
                if d.get('year'):
                    parts.append(str(d['year']))
                else:
                    parts.append('0000')
                parts.append('%02d' % d.get('month', 1))
                parts.append('%02d' % d.get('day', 1))
                self.set_birthday('-'.join(parts))

        events = person.get('events', [])
        for ev in events:
            if ev.get('type') == 'anniversary':
                d = ev.get('date', {})
                if d:
                    parts = []
                    if d.get('year'):
                        parts.append(str(d['year']))
                    else:
                        parts.append('0000')
                    parts.append('%02d' % d.get('month', 1))
                    parts.append('%02d' % d.get('day', 1))
                    self.set_anniv('-'.join(parts))

    def _snarf_websites_from_person (self, person):
        for url in person.get('urls', []):
            href = url.get('value', '')
            if not href:
                continue
            utype = (url.get('type') or '').lower()
            if utype == 'homePage' or utype == 'home':
                self.add_web_home(href)
            elif utype == 'work':
                self.add_web_work(href)
            else:
                self.add_web_home(href)

    def _snarf_ims_from_person (self, person):
        for im in person.get('imClients', []):
            username = im.get('username', '')
            if not username:
                continue

            proto = (im.get('protocol') or '').lower()
            label = IM_PROTO_LABEL.get(proto, proto if proto else 'Other')

            self.add_im(label, username)

            metadata = im.get('metadata', {})
            if metadata.get('primary'):
                self.set_im_prim(label)

    def _snarf_sync_tags_from_person (self, person):
        udps = person.get('userDefined', [])
        if udps:
            keyprefix = (self.get_config().get_label_prefix() +
                         self.get_config().get_label_separator())
            stgs = folder_gc.get_udps_by_key_prefix(udps, keyprefix)
            self.set_sync_tags(stgs)

    def _snarf_custom_props_from_person (self, person):
        stag_re = (self.get_config().get_label_prefix() +
                   self.get_config().get_label_separator())
        for ep in person.get('userDefined', []):
            key = ep.get('key', '')
            val = ep.get('value', '')
            if key == 'created':
                self.set_created(val)
            elif not re.search(stag_re, key):
                self.add_custom(key, val)

    ##
    ## Internal functions — add (Contact props → Person dict)
    ##

    def _is_valid_ph (self, phone, ptype):
        phone = phone.strip()
        valid = True
        if phone in ('', '-', '_'):
            valid = False
        if not valid:
            logging.info('Invalid %s number for contact %s. Skipping field',
                         ptype, self.get_name())
        return valid

    def _is_invalid_ph (self, phone, ptype):
        return not self._is_valid_ph(phone, ptype)

    def _add_names_gender_to_person (self, person):
        name = {}

        text = self.get_firstname()
        if text:
            name['givenName'] = text

        text = self.get_lastname()
        if text:
            name['familyName'] = text

        text = self.get_middlename()
        if text:
            name['middleName'] = text

        text = self.get_name()
        if text:
            name['displayName'] = text

        text = self.get_suffix()
        if text:
            name['honorificSuffix'] = text

        text = self.get_prefix()
        if text:
            name['honorificPrefix'] = text

        if name:
            person['names'] = [name]

        text = self.get_nickname()
        if text:
            person['nicknames'] = [{'value': text}]

        text = self.get_gender()
        if text:
            person['genders'] = [{'value': text}]

    def _add_notes_to_person (self, person):
        notes = self.get_notes()
        if notes:
            person['biographies'] = [{'value': notes[0]}]

    def _add_group_membership_to_person (self, person):
        gid = self.get_folder().get_itemid()
        memberships = [{
            'contactGroupMembership': {
                'contactGroupResourceName': gid
            }
        }]

        js = self.get_custom('gids')
        if js:
            js = js.replace('\\', '')
            gids = demjson.decode(js)
            for g in gids:
                memberships.append({
                    'contactGroupMembership': {
                        'contactGroupResourceName': g
                    }
                })

        person['memberships'] = memberships

    def _add_emails_to_person (self, person):
        email_prim = self.get_email_prim()
        emails = []

        for email in self.get_email_home():
            if not email:
                continue
            entry = {'value': email, 'type': TYPE_HOME}
            if email == email_prim:
                entry.setdefault('metadata', {})['primary'] = True
            emails.append(entry)

        for email in self.get_email_work():
            if not email:
                continue
            entry = {'value': email, 'type': TYPE_WORK}
            if email == email_prim:
                entry.setdefault('metadata', {})['primary'] = True
            emails.append(entry)

        for email in self.get_email_other():
            if not email:
                continue
            entry = {'value': email, 'type': TYPE_OTHER}
            if email == email_prim:
                entry.setdefault('metadata', {})['primary'] = True
            emails.append(entry)

        if emails:
            person['emailAddresses'] = emails

    def _add_postal_to_person (self, person):
        postals = self.get_postal(as_array=True)
        addresses = []

        for label, postal in postals:
            if not postal:
                continue

            addr = {'type': label}

            if postal.get('street'):
                addr['streetAddress'] = postal['street']
            if postal.get('city'):
                addr['city'] = postal['city']
            if postal.get('state'):
                addr['region'] = postal['state']
            if postal.get('country'):
                addr['country'] = postal['country']
            if postal.get('zip'):
                addr['postalCode'] = postal['zip']
            if postal.get('formatted_address'):
                addr['formattedValue'] = postal['formatted_address']

            if self.is_postal_prim(label):
                addr.setdefault('metadata', {})['primary'] = True

            addresses.append(addr)

        if addresses:
            person['addresses'] = addresses

    def _add_org_details_to_person (self, person):
        company = self.get_company()
        title   = self.get_title()
        dept    = self.get_dept()

        if company or title or dept:
            org = {'type': TYPE_WORK}
            if company:
                org['name'] = company
            if title:
                org['title'] = title
            if dept:
                org['department'] = dept

            person['organizations'] = [org]

    def _add_phones_and_faxes_to_person (self, person):
        ph_prim  = self.get_phone_prim()
        fax_prim = self.get_fax_prim()
        phones = []

        for label, ph in self.get_phone_home():
            if not ph or self._is_invalid_ph(ph, 'Home'):
                continue
            entry = {'value': ph, 'type': TYPE_HOME}
            if ph == ph_prim:
                entry.setdefault('metadata', {})['primary'] = True
            phones.append(entry)

        for label, ph in self.get_phone_work():
            if not ph or self._is_invalid_ph(ph, 'Work'):
                continue
            entry = {'value': ph, 'type': TYPE_WORK}
            if ph == ph_prim:
                entry.setdefault('metadata', {})['primary'] = True
            phones.append(entry)

        for label, ph in self.get_phone_other():
            if not ph or self._is_invalid_ph(ph, 'Other'):
                continue
            entry = {'value': ph, 'type': TYPE_OTHER}
            if ph == ph_prim:
                entry.setdefault('metadata', {})['primary'] = True
            phones.append(entry)

        for label, ph in self.get_phone_mob():
            if not ph or self._is_invalid_ph(ph, 'Mobile'):
                continue
            entry = {'value': ph, 'type': TYPE_MOBILE}
            if ph == ph_prim:
                entry.setdefault('metadata', {})['primary'] = True
            phones.append(entry)

        for label, fa in self.get_fax_home():
            if not fa or self._is_invalid_ph(fa, 'Home Fax'):
                continue
            entry = {'value': fa, 'type': TYPE_HOME_FAX}
            if fa == fax_prim:
                entry.setdefault('metadata', {})['primary'] = True
            phones.append(entry)

        for label, fa in self.get_fax_work():
            if not fa or self._is_invalid_ph(fa, 'Work Fax'):
                continue
            entry = {'value': fa, 'type': TYPE_WORK_FAX}
            if fa == fax_prim:
                entry.setdefault('metadata', {})['primary'] = True
            phones.append(entry)

        if phones:
            person['phoneNumbers'] = phones

    def _add_dates_to_person (self, person):
        dt = self.get_birthday()
        if dt:
            date = self._parse_date_str(dt)
            if date:
                person['birthdays'] = [{'date': date}]

        dt = self.get_anniv()
        if dt:
            date = self._parse_date_str(dt)
            if date:
                person['events'] = [{'date': date, 'type': 'anniversary'}]

    def _parse_date_str (self, dt_str):
        """Parse a date string like '2000-01-15' into a People API Date
        dict like {'year': 2000, 'month': 1, 'day': 15}."""
        try:
            parts = dt_str.split('-')
            d = {}
            if len(parts) >= 1 and parts[0] != '0000':
                d['year'] = int(parts[0])
            if len(parts) >= 2:
                d['month'] = int(parts[1])
            if len(parts) >= 3:
                d['day'] = int(parts[2])
            return d if d else None
        except (ValueError, AttributeError):
            return None

    def _add_websites_to_person (self, person):
        urls = []

        for web in self.get_web_home():
            if web:
                urls.append({'value': web, 'type': 'homePage'})

        for web in self.get_web_work():
            if web:
                urls.append({'value': web, 'type': 'work'})

        if urls:
            person['urls'] = urls

    def _add_ims_to_person (self, person):
        im_prim = self.get_im_prim()
        ims = []

        for label, addr in self.get_im().items():
            proto = IM_LABEL_PROTO.get(label, label)

            entry = {'username': addr, 'protocol': proto, 'type': TYPE_OTHER}
            if im_prim == label:
                entry.setdefault('metadata', {})['primary'] = True
            ims.append(entry)

        if ims:
            person['imClients'] = ims

    def _add_sync_tags_to_person (self, person):
        udps = person.get('userDefined', [])

        for key, val in self.get_sync_tags().items():
            udps.append({'key': key, 'value': val})

        if udps:
            person['userDefined'] = udps

    def _add_custom_props_to_person (self, person):
        udps = person.get('userDefined', [])

        c = self.get_created()
        if c:
            val = c.isoformat() if isinstance(c, datetime) else c
            udps.append({'key': 'created', 'value': val})

        for key, val in self.get_custom().items():
            if val:
                val = val.isoformat() if isinstance(val, datetime) else val
                udps.append({'key': key, 'value': val})

        if udps:
            person['userDefined'] = udps
