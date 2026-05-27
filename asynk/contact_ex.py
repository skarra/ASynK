##
## Created : Wed Apr 02 11:31:26 IST 2014
## SPDX-FileCopyrightText: 2014-2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
## ####
##
## This file extends the Contact base class to implement an Exchange Contact
## item while implementing the base class methods.
##
## Rewritten for Microsoft Graph API, replacing the legacy pyews EWS client.
##

import logging

from contact import Contact
import utils
import demjson3 as demjson

## The name of the Open Extension used to store ASynK-specific data on each
## contact in Exchange Online. This holds sync tags, custom overflow data,
## and fields that don't have a native Graph API property.
ASYNK_EXTENSION_NAME = 'com.asynk.syncdata'

class EXContactError(Exception):
    pass

class EXContact(Contact):
    prop_update_t = utils.enum('PROP_REPLACE', 'PROP_APPEND')

    def __init__ (self, folder, graph_con=None, con=None, con_itemid=None):
        """Constructor for EXContact. The starting properties of the contact
        can be initialized either from an existing Contact object, or from a
        Microsoft Graph contact dict. It is an error to provide both.
        """

        if (graph_con and con):
            raise EXContactError(
                'Both graph_con and con cannot be specified in EXContact()')

        Contact.__init__(self, folder, con)

        conf = self.get_config()
        if con:
            if con_itemid:
                self.set_itemid(con_itemid)
            else:
                logging.debug('Potential new EXContact: %s', con.get_disp_name())

        self.set_graph_con(graph_con)
        if graph_con is not None:
            self.init_props_from_graph_contact(graph_con)

    ##
    ## First the inherited abstract methods from the base classes
    ##

    def save (self):
        """Saves the current contact on the server. For now we are only
        handling a new contact creation scenario. The protocol for updates is
        different."""

        logging.debug('Saving contact (%s) to server...', self.get_disp_name())
        graph_dict = self.to_graph_dict()
        client = self.get_db().get_graph_client()
        folder_id = self.get_folder().get_itemid()

        itemid = self.get_itemid()
        if itemid:
            resp = client.update_contact(itemid, graph_dict)
        else:
            resp = client.create_contact(folder_id, graph_dict)
            if resp and 'id' in resp:
                self.set_itemid(resp['id'])

        ## Write the extension data (sync tags + custom overflow)
        if resp and 'id' in resp:
            self._write_extension(resp['id'])

        logging.debug('Saving contact to server...done')

    ##
    ## Now onto the non-abstract methods.
    ##

    def get_parent_folder_id (self):
        """Fetch and return the itemid of the parent folder of this contact in
        the Exchange store. This will be None if this is a new contact that
        has not yet been written to the server"""

        try:
            return self._get_att('parentid')
        except Exception as e:
            return None

    def set_parent_folder_id (self, pfid):
        return self._set_att('parentid', pfid)

    ##
    ## And now, the internal methods
    ##

    def init_props_from_graph_contact (self, gc):
        """Initialize ASynK contact properties from a Microsoft Graph API
        contact JSON dict. This is the Graph API equivalent of the former
        init_props_from_ews_con()."""

        ## Read extension data first, since custom props affect phone/fax/IM
        ## label restoration later.
        self._snarf_extension_from_graph_con(gc)

        self._snarf_itemid_from_graph_con(gc)
        self._snarf_names_gender_from_graph_con(gc)
        self._snarf_notes_from_graph_con(gc)
        self._snarf_emails_from_graph_con(gc)
        self._snarf_postal_from_graph_con(gc)
        self._snarf_org_details_from_graph_con(gc)
        self._snarf_phones_and_faxes_from_graph_con(gc)
        self._snarf_dates_from_graph_con(gc)
        self._snarf_websites_from_graph_con(gc)
        self._snarf_ims_from_graph_con(gc)
        self._snarf_sync_tags_from_graph_con(gc)

    def to_graph_dict (self):
        """Return a JSON-serializable dict representing this contact in
        Microsoft Graph API format. This is the Graph API equivalent of the
        former init_ews_con_from_props()."""

        gc = {}

        self._add_names_gender_to_graph_dict(gc)
        self._add_notes_to_graph_dict(gc)
        self._add_emails_to_graph_dict(gc)
        self._add_postal_to_graph_dict(gc)
        self._add_org_details_to_graph_dict(gc)
        self._add_phones_to_graph_dict(gc)
        self._add_dates_to_graph_dict(gc)
        self._add_websites_to_graph_dict(gc)
        self._add_ims_to_graph_dict(gc)

        return gc

    def get_extension_data (self):
        """Build and return the Open Extension dict containing all data that
        doesn't fit into native Graph API contact fields: sync tags, custom
        overflow, and unsupported fields like gender, anniversary, alias,
        personal homepage, faxes, etc."""

        ext = {}

        ## Sync tags
        stags = self.get_sync_tags()
        if stags:
            ext['syncTags'] = stags

        ## Custom overflow data (phones labels, fax labels, IM labels, extra
        ## web URLs, and anything else stashed in the custom dict)
        custom = self.get_custom()
        if custom:
            ext['customData'] = custom

        ## Fields with no native Graph API property
        gender = self.get_gender()
        if gender:
            ext['gender'] = gender

        anniv = self.get_anniv()
        if anniv:
            ext['anniversary'] = anniv

        alias = self.get_custom('alias')
        if alias:
            ext['alias'] = alias

        personal_hp = self.get_web_home()
        if personal_hp and len(personal_hp) > 0:
            ext['personalHomePage'] = personal_hp[0]

        ## Faxes - no native Graph field
        fax_home = self.get_fax_home()
        if fax_home:
            ext['faxHome'] = fax_home

        fax_work = self.get_fax_work()
        if fax_work:
            ext['faxWork'] = fax_work

        return ext

    ## ----------------------------------------------------------------
    ## Internal: Read from Graph contact dict → ASynK props
    ## ----------------------------------------------------------------

    def _snarf_itemid_from_graph_con (self, gc):
        self.set_parent_folder_id(gc.get('parentFolderId'))
        self.set_itemid(gc.get('id'))
        self.set_changekey(gc.get('changeKey'))

    def _snarf_names_gender_from_graph_con (self, gc):
        self.set_fileas(gc.get('fileAs'))
        self.set_name(gc.get('displayName'))
        self.set_prefix(gc.get('title'))
        self.set_firstname(gc.get('givenName'))
        self.set_lastname(gc.get('surname'))
        self.set_middlename(gc.get('middleName'))
        self.set_suffix(gc.get('generation'))
        self.set_nickname(gc.get('nickName'))

        ## Gender is stored in Open Extension, not a native Graph field.
        ## It's read in _snarf_extension_from_graph_con().

        ## Alias is stored in Open Extension as well.
        ## Restored in _snarf_extension_from_graph_con().

    def _snarf_notes_from_graph_con (self, gc):
        notes = gc.get('personalNotes')
        if notes:
            self.add_notes(notes)

    def _snarf_emails_from_graph_con (self, gc):
        """Classify each email address as home/work/other and store them.
        Graph API provides emailAddresses as an array of {name, address}
        objects. Classification is done based on domain as per config."""

        domains = self.get_email_domains()
        emails = gc.get('emailAddresses', [])

        for entry in emails:
            addr = entry.get('address')
            if not addr:
                continue

            home, work, other = utils.classify_email_addr(addr, domains)

            if home:
                self.add_email_home(addr)
            elif work:
                self.add_email_work(addr)
            elif other:
                self.add_email_other(addr)
            else:
                self.add_email_work(addr)

    def _snarf_postal_from_graph_con (self, gc):
        """Read postal addresses from the Graph contact. Graph API provides
        homeAddress, businessAddress, and otherAddress as structured objects."""

        addr_map = {
            'homeAddress'     : 'home',
            'businessAddress' : 'work',
            'otherAddress'    : 'other',
        }

        for graph_field, asynk_type in addr_map.items():
            addr = gc.get(graph_field)
            if not addr:
                continue

            ## Graph address fields: street, city, state, countryOrRegion,
            ## postalCode
            postal_dict = {}
            if addr.get('street'):
                postal_dict['street'] = addr['street']
            if addr.get('city'):
                postal_dict['city'] = addr['city']
            if addr.get('state'):
                postal_dict['state'] = addr['state']
            if addr.get('countryOrRegion'):
                postal_dict['country'] = addr['countryOrRegion']
            if addr.get('postalCode'):
                postal_dict['zip'] = addr['postalCode']

            if postal_dict:
                label = '%s Address' % asynk_type.capitalize()
                existing = self.get_postal(asynk_type)
                if existing:
                    existing.append((label, postal_dict))
                else:
                    self.set_postal([(label, postal_dict)], asynk_type)

    def _snarf_org_details_from_graph_con (self, gc):
        self.set_title(gc.get('jobTitle'))
        self.set_company(gc.get('companyName'))
        self.set_dept(gc.get('department'))

    def _snarf_phones_and_faxes_from_graph_con (self, gc):
        """Read phones from Graph contact. Graph API provides:
        - businessPhones: array of strings
        - homePhones: array of strings
        - mobilePhone: single string

        Phone labels and fax numbers are restored from the Open Extension
        custom data (read earlier in _snarf_extension_from_graph_con)."""

        ph_labels = self.get_custom('phones')
        fa_labels = self.get_custom('faxes')

        ## Home phones
        for i, num in enumerate(gc.get('homePhones', [])):
            if ph_labels and num in ph_labels.get('home', {}):
                label = ph_labels['home'][num]
            else:
                label = 'Home' if i == 0 else 'Home%d' % (i+1)
            self.add_phone_home((label, num))

        ## Business phones
        for i, num in enumerate(gc.get('businessPhones', [])):
            if ph_labels and num in ph_labels.get('work', {}):
                label = ph_labels['work'][num]
            else:
                label = 'Work' if i == 0 else 'Work%d' % (i+1)
            self.add_phone_work((label, num))

        ## Mobile phone
        mob = gc.get('mobilePhone')
        if mob:
            if ph_labels and mob in ph_labels.get('mob', {}):
                label = ph_labels['mob'][mob]
            else:
                label = 'Mobile'
            self.add_phone_mob((label, mob))

        ## Other phones (from custom overflow, since Graph has no native
        ## "other phone" field)
        if ph_labels:
            for num, label in ph_labels.get('other', {}).items():
                self.add_phone_other((label, num))

        ## Primary phone (from custom overflow)
        if ph_labels and 'prim' in ph_labels:
            self.set_phone_prim(ph_labels['prim'])

        ## Faxes are entirely in the Open Extension
        ## They were already restored from extension data, but read them
        ## here if they came through that path.

        self.del_custom('phones')
        self.del_custom('faxes')

    def _snarf_dates_from_graph_con (self, gc):
        self.set_created(gc.get('createdDateTime'))
        self.set_updated(gc.get('lastModifiedDateTime'))
        bday = gc.get('birthday')
        if bday and 'T' in bday:
            bday = bday.split('T')[0]
        self.set_birthday(bday)
        ## Anniversary is stored in Open Extension, read earlier.

    def _snarf_websites_from_graph_con (self, gc):
        """Graph API only has businessHomePage as a native field.
        personalHomePage is stored in the Open Extension."""

        biz_hp = gc.get('businessHomePage')
        if biz_hp:
            self.add_web_work(biz_hp)

        ## personalHomePage was already restored from extension data.

        ## Additional web addresses from custom overflow
        webs = self.get_custom('webs')
        if webs:
            for home_url in webs.get('home', []):
                self.add_web_home(home_url)
            for work_url in webs.get('work', []):
                self.add_web_work(work_url)
            self.del_custom('webs')

    def _snarf_ims_from_graph_con (self, gc):
        """Graph API provides imAddresses as an array of strings."""

        im_labels = self.get_custom('ims')
        ims = gc.get('imAddresses', [])

        for i, addr in enumerate(ims):
            if im_labels and addr in im_labels:
                label = im_labels[addr]
            else:
                label = 'ImAddress%d' % (i+1)

            if i == 0:
                self.set_im_prim(label)

            self.add_im(label, addr)

        self.del_custom('ims')

    def _snarf_sync_tags_from_graph_con (self, gc):
        """Sync tags are stored in the Open Extension. They were already
        read in _snarf_extension_from_graph_con()."""
        pass

    def _snarf_extension_from_graph_con (self, gc):
        """Read the ASynK Open Extension data from the Graph contact.
        The extension may be inline (if $expand=extensions was used) or
        may need a separate fetch."""

        ext = None

        ## Check inline extensions first
        extensions = gc.get('extensions', [])
        for e in extensions:
            if e.get('id', '').endswith(ASYNK_EXTENSION_NAME) or \
               e.get('extensionName') == ASYNK_EXTENSION_NAME:
                ext = e
                break

        if ext is None:
            ## Try fetching from server if we have an ID
            contact_id = gc.get('id')
            if contact_id:
                client = self._get_graph_client()
                if client:
                    ext = client.get_extension(contact_id,
                                               ASYNK_EXTENSION_NAME)

        if ext is None:
            return

        ## Restore sync tags
        stags = ext.get('syncTags', {})
        for name, val in stags.items():
            self.update_sync_tags(name, val)

        ## Restore custom overflow data
        custom = ext.get('customData', {})
        if custom:
            self.update_custom(custom)

        ## Restore fields without native Graph properties
        gender = ext.get('gender')
        if gender:
            self.set_gender(gender)

        anniv = ext.get('anniversary')
        if anniv:
            self.set_anniv(anniv)

        alias = ext.get('alias')
        if alias:
            self.add_custom('alias', alias)

        personal_hp = ext.get('personalHomePage')
        if personal_hp:
            self.add_web_home(personal_hp)

        fax_home = ext.get('faxHome')
        if fax_home:
            for fax in fax_home:
                if isinstance(fax, (list, tuple)) and len(fax) == 2:
                    self.add_fax_home(tuple(fax))

        fax_work = ext.get('faxWork')
        if fax_work:
            for fax in fax_work:
                if isinstance(fax, (list, tuple)) and len(fax) == 2:
                    self.add_fax_work(tuple(fax))

    ## ----------------------------------------------------------------
    ## Internal: Write ASynK props → Graph contact dict
    ## ----------------------------------------------------------------

    def _add_names_gender_to_graph_dict (self, gc):
        fn = self.get_firstname()
        ln = self.get_lastname()

        if fn:
            gc['givenName'] = fn
        if ln:
            gc['surname'] = ln

        mn = self.get_middlename()
        if mn:
            gc['middleName'] = mn

        prefix = self.get_prefix()
        if prefix:
            gc['title'] = prefix

        suffix = self.get_suffix()
        if suffix:
            gc['generation'] = suffix

        nick = self.get_nickname()
        if nick:
            gc['nickName'] = nick

        fileas = self.get_fileas()
        if fileas:
            gc['fileAs'] = fileas

        name = self.get_name()
        if name:
            gc['displayName'] = name

        ## Gender goes into Open Extension, not the Graph dict.
        ## Alias goes into Open Extension via custom dict.

    def _add_notes_to_graph_dict (self, gc):
        n = self.get_notes()
        if n and len(n) > 0:
            gc['personalNotes'] = n[0]
            ## If there are multiple notes, the rest are preserved in custom
            ## overflow (handled by the abstract base)

    def _add_emails_to_graph_dict (self, gc):
        """Graph API supports unlimited email addresses as an array of
        {name, address} objects. No more 3-email limit!"""

        emails = []

        ## Primary email first if set
        prim = self.get_email_prim()
        if prim:
            emails.append({'address': prim, 'name': ''})

        for addr in self.get_email_home():
            if addr != prim:
                emails.append({'address': addr, 'name': ''})

        for addr in self.get_email_work():
            if addr != prim:
                emails.append({'address': addr, 'name': ''})

        for addr in self.get_email_other():
            if addr != prim:
                emails.append({'address': addr, 'name': ''})

        if emails:
            gc['emailAddresses'] = emails

    def _add_postal_to_graph_dict (self, gc):
        """Write postal addresses to Graph contact dict. Graph API supports
        three addresses: homeAddress, businessAddress, otherAddress."""

        type_to_field = {
            'home'  : 'homeAddress',
            'work'  : 'businessAddress',
            'other' : 'otherAddress',
        }

        for asynk_type, graph_field in type_to_field.items():
            addrs = self.get_postal(asynk_type)
            if not addrs or len(addrs) == 0:
                continue

            ## Use the first address of each type for the native field.
            ## Additional addresses of the same type are preserved in
            ## custom overflow (the Contact base class handles this).
            label, addr_dict = addrs[0]

            graph_addr = {}
            if addr_dict.get('street'):
                graph_addr['street'] = addr_dict['street']
            if addr_dict.get('city'):
                graph_addr['city'] = addr_dict['city']
            if addr_dict.get('state'):
                graph_addr['state'] = addr_dict['state']
            if addr_dict.get('country'):
                graph_addr['countryOrRegion'] = addr_dict['country']
            if addr_dict.get('zip'):
                graph_addr['postalCode'] = addr_dict['zip']

            if graph_addr:
                gc[graph_field] = graph_addr

    def _add_org_details_to_graph_dict (self, gc):
        dept = self.get_dept()
        if dept:
            gc['department'] = dept

        company = self.get_company()
        if company:
            gc['companyName'] = company

        title = self.get_title()
        if title:
            gc['jobTitle'] = title

    def _add_phones_to_graph_dict (self, gc):
        """Write phone numbers to Graph dict. Also stash phone labels and
        overflow data (other phones, primary phone) in the custom dict for
        preservation.

        Graph API fields:
        - homePhones: array of strings
        - businessPhones: array of strings
        - mobilePhone: single string
        """

        ## Build label-preservation custom dict
        cust = {'mob': {}, 'home': {}, 'work': {}, 'other': {}}

        ## Home phones
        home_nums = []
        for label, num in self.get_phone_home():
            home_nums.append(num)
            cust['home'][num] = label
        if home_nums:
            gc['homePhones'] = home_nums

        ## Work phones
        work_nums = []
        for label, num in self.get_phone_work():
            work_nums.append(num)
            cust['work'][num] = label
        if work_nums:
            gc['businessPhones'] = work_nums

        ## Mobile phone (Graph only supports one)
        mob = self.get_phone_mob()
        if mob and len(mob) >= 1:
            gc['mobilePhone'] = mob[0][1]
            for label, num in mob:
                cust['mob'][num] = label

        ## Other phones — no native Graph field, stored in custom overflow
        for label, num in self.get_phone_other():
            cust['other'][num] = label

        ## Primary phone — no native Graph field
        prim = self.get_phone_prim()
        if prim:
            cust['prim'] = prim

        ## Stash labels so they survive round-trips
        self.add_custom('phones', cust)

        ## Faxes — no native Graph field, stored entirely in extension
        ## (handled in get_extension_data)

    def _add_dates_to_graph_dict (self, gc):
        bd = self.get_birthday()
        if bd:
            gc['birthday'] = bd

        ## Anniversary goes into Open Extension (no native field).

    def _add_websites_to_graph_dict (self, gc):
        """Graph API only has businessHomePage as a native field.
        Personal homepage and extra URLs go into the Open Extension."""

        cus_web = {'home': [], 'work': []}

        web = self.get_web_work()
        if web and len(web) > 0:
            gc['businessHomePage'] = web[0]
            if len(web) > 1:
                cus_web['work'] = web[1:]

        ## Personal homepage is stored in extension (handled in
        ## get_extension_data). But any additional home URLs beyond
        ## the first go into custom overflow.
        web = self.get_web_home()
        if web and len(web) > 1:
            cus_web['home'] = web[1:]

        if cus_web['home'] or cus_web['work']:
            self.add_custom('webs', cus_web)

    def _add_ims_to_graph_dict (self, gc):
        """Graph API provides imAddresses as an array of strings."""

        cust = {}
        ims_list = []

        for label, value in self.get_im().items():
            ims_list.append(value)
            cust[value] = label

        if ims_list:
            gc['imAddresses'] = ims_list

        if cust:
            self.add_custom('ims', cust)

    ## ----------------------------------------------------------------
    ## Internal: Extension (sync tags + custom data) write
    ## ----------------------------------------------------------------

    def _write_extension (self, contact_id):
        """Write sync tags and custom overflow to the contact's Open
        Extension on the server."""

        client = self._get_graph_client()
        if client is None:
            return

        ext_data = self.get_extension_data()
        if ext_data:
            client.set_extension(contact_id, ASYNK_EXTENSION_NAME, ext_data)

    def _get_graph_client (self):
        """Get the GraphContactsClient from the parent DB, or None."""

        try:
            return self.get_db().get_graph_client()
        except Exception:
            return None

    ##
    ## some additional get and set methods
    ##

    def get_changekey (self):
        try:
            return self._get_att('ck')
        except KeyError as e:
            return None

    def set_changekey (self, ck):
        return self._set_att('ck', ck)

    def get_graph_con (self):
        return self._get_att('graph_con')

    def set_graph_con (self, gc):
        return self._set_att('graph_con', gc)

    def get_ews_con (self):
        """Backward compat alias."""
        return self.get_graph_con()

    def set_ews_con (self, ec):
        """Backward compat alias."""
        return self.set_graph_con(ec)
