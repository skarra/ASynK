#!/usr/bin/python
## 
## gc_wrapper.py
##
## Created       : Thu Jul 07 14:47:54  2011
## Last Modified : Wed Nov 30 18:30:20 IST 2011
## 
## Copyright (C) 2011 by Sriram Karra <karra.etc@gmail.com>
## All rights reserved.
## 
## Licensed under the GPL v3
## 

import sys, getopt, logging
import getpass
import atom
import gdata.contacts.data
import gdata.contacts.client
import base64
import xml.dom.minidom

import utils, time, datetime

from state import Config

def get_udp_by_key (udps, key):
    
    for ep in udps:
        if ep.key == key:   
            if ep.value:
                return ep.value
            else:
                value = 'Hrrmph. '
                print 'Value: ', value

    return None

class GC (object):
    """GC object is a wrapper for a Google Contacts stream API."""

    def __init__(self, config, email, password):
        """Constructor for the GC wrapper object.

        Takes an email and password corresponding to a gmail account,
        and can do various things to the contact list such as upload,
        and modify, etc.
        """

        self.config = config
        self.gd_client = gdata.contacts.client.ContactsClient(source='Outlook-Android-Contacts-Sync')
        self.gd_client.ClientLogin(email, password, self.gd_client.source)

        if not self.config.get_gid():
            logging.info('First use of application. Creating group...')
            gn = self.config.get_gn()
            if not gn:
                gn = 'Gout'
                self.config.set_gn(gn, False)
                logging.info('Using default Gmail Contacts Group: Gout')

            gc_gid = self.create_group(gn)
            self.config.set_gid(gc_gid)


    def query_contact (self, gcid):
        print '===== Querying ======'
        query = gdata.contacts.client.ContactsQuery({'entryID':gcid,
                                                     'entryid':gcid,
                                                     'entry_id':gcid})
        query.entryid = query.entry_id = gcid
        query.entryID = query.entryId  = gcid
#        cexml=xml.dom.minidom.parseString('%s'%query)
#        print cexml.toprettyxml()

        print'\n===\n'
        feed = self.gd_client.GetContacts(q = query)
        return feed

    def clear_group (self, gentry, gid=None):
        """Delete all contacts in specified group. """

        if not gid:
            if not gentry:
                return
            gid = gentry.id.text

        feed = self._get_group_feed(gid)

        # A batch operation would be much faster... should implement
        # someday
        for con in feed.entry:
            logging.info('Deleting ID: %s; Name: %s...', con.id.text,
                         con.name.full_name.text if con.name else '')
            self.gd_client.Delete(con)

  
    def clear_sync_state (self):
        """Clear up all prior sync related artifacts"""
        gentry = self.find_group(self.config.get_gn(), 'entry')
        if gentry:
            self.clear_group(gentry)
            logging.info('Deleting Group: %s...', gentry.id.text)
            self.gd_client.delete_group(gentry)
        else:
            logging.info('Group \'%s\' not found', self.config.get_gn())

    def get_groups (self):
        feed = self.gd_client.GetGroups()
        return feed

    def print_groups (self):
        feed = self.get_groups()
  
        if not feed.entry:
            print 'No groups for user'
        for i, entry in enumerate(feed.entry):
            print '\n%s %s' % (i+1, entry.title.text)
            if entry.content:
                print '  Yeah: %s' % (entry.content.text)

            print '  Group ID: %s' % entry.id.text
  
            # Display extended properties.
            for ep in entry.extended_property:
                if ep.value:
                    value = ep.value
                else:
                    value = ep.GetXmlBlob()
                    print '  EP %s: %s' % (ep.name, value)


    def find_group (self, title, ret_type='id'):
        """Find the group with the given name.
  
        Takes a group title, and returns the Group ID if found. Returns
        None if the group cannot be found.
        """
  
        feed = self.gd_client.GetGroups()
    
        if not feed.entry:
            logging.info('\nGroup (%s) not found: there are no groups!',
                          title)
            return None
    
        for i, entry in enumerate(feed.entry):
            if entry.title.text == title:
                if ret_type == 'entry':
                    return entry
                else:
                    return entry.id.text

        return None

    def create_group (self, title='Default News'):
        gn = gdata.data.Name(name=title)
        new_group = gdata.contacts.data.GroupEntry(name=gn)
        new_group.title = atom.data.Title(text=title)
    
        entry = self.gd_client.create_group(new_group)
    
        if entry:
            logging.info('Successfully created group. ID: %s',
                         entry.id.text)
            return entry.id.text
        else:
            logging.error('Could not create Group \'%s\'', gn)
            return None

    def is_valid_phone_number (self, phone, type, name):
        phone = phone.strip()
        valid = True
        if (phone == '' or phone == '-' or phone == '_'):
            valid = False
   
        if not valid:
            logging.info('Invalid %12s number for contact %s. Skipping field',
                         type, name)

        return valid

    def create_contact_entry (self, entryid, name, gnames, emails=None, 
                              gids=None, company=None, notes=None,
                              title=None, dept=None, ph_prim=None,
                              postal=None, ph_mobile=None, ph_home=None,
                              ph_work=None, ph_home2=None,
                              ph_work2=None, ph_other=None,
                              fax_home=None, fax_work=None,
                              fax_prim=None, birthday=None, anniv=None,
                              nickname=None, gender=None,
                              web_home=None, web_work=None,
                              gcid=None):
        if not gids:
            gids = []
            for gname in gnames:
                gid = self.find_group(gname)
      
                if not gid:
                    gid = self.create_group(gname)
      
                gids.append(gid)
            
        fn = gdata.data.FullName(text=name)
        n  = gdata.data.Name(full_name=fn)
    
        # First create a bare bones contact structure. We will populate
        # the fields as we go along
    
        new_contact = gdata.contacts.data.ContactEntry(name=n)
        new_contact.content = atom.data.Content(text=notes)
    
        if gcid:
            id_entry = atom.data.Id(text=gcid)
            new_contact.id = id_entry

        # Set up the group memberships
        for gid in gids:
            gidm = gdata.contacts.data.GroupMembershipInfo(href=gid)
            new_contact.group_membership_info.append(gidm)
    
        # Store the entryid as a User defined property. Note that the
        # MAPI EntryID is a binary value; so we base64 encode it first
        new_contact = self.add_olid_to_ce(new_contact, entryid)

        # Populate the email addresses
        if emails:
          # Create a work email address for the contact and use as
          # primary.
          i = 0
          for email in emails:
              prim = 'true'
              if i > 0:
                  prim = 'false'
      
              em = gdata.data.Email(address=email, primary=prim,
                                    rel=gdata.data.WORK_REL)
              new_contact.email.append(em)
              i += 1
    
        # Populate the postal address. We need to extract out the
        # relevant bits and populate in a structured fashion. For now
        # dump the entire thing into the 'street' component.
        if postal:
            strt = gdata.data.Street(text=postal)
            add  = gdata.data.StructuredPostalAddress(
                street=strt, primary='true',
                rel=gdata.data.WORK_REL)
            new_contact.structured_postal_address = [add]
          
        # Populate the organizational details
        if company:
            org_name  = gdata.data.OrgName(text=company)
            org_title = None
            org_dept  = None
      
            if title:
                org_title = gdata.data.OrgTitle(text=title)
            if dept:
                org_dept  = gdata.data.OrgDepartment(text=dept)
      
            org = gdata.data.Organization(primary='true',
                                          name=org_name,
                                          title=org_title,
                                          department=org_dept,
                                          rel=gdata.data.WORK_REL)
            new_contact.organization = org
    
        # Populate the phone numbers
        if ph_mobile and self.is_valid_phone_number(ph_mobile, 'Mobile', name):
            prim = 'true' if ph_prim == ph_mobile else 'false'
            mobile = gdata.data.PhoneNumber(text=ph_mobile,
                                            primary=prim,
                                            rel=gdata.data.MOBILE_REL)
            new_contact.phone_number.append(mobile)
    
        if ph_home and self.is_valid_phone_number(ph_home, 'Home', name):
            prim = 'true' if ph_prim == ph_home else 'false'
            home = gdata.data.PhoneNumber(text=ph_home,
                                          primary=prim,
                                          rel=gdata.data.HOME_REL)
            new_contact.phone_number.append(home)
    
        if ph_home2 and self.is_valid_phone_number(ph_home2, 'Home 2', name):
            prim = 'true' if ph_prim == ph_home2 else 'false'
            home = gdata.data.PhoneNumber(text=ph_home2,
                                          primary=prim,
                                          rel=gdata.data.HOME_REL)
            new_contact.phone_number.append(home)

        if ph_work and self.is_valid_phone_number(ph_work, 'Business', name):
            prim = 'true' if ph_prim == ph_work else 'false'
            work = gdata.data.PhoneNumber(text=ph_work,
                                          primary=prim,
                                          rel=gdata.data.WORK_REL)
            new_contact.phone_number.append(work)

        if ph_work2 and self.is_valid_phone_number(ph_work2, 'Business 2', name):
            prim = 'true' if ph_prim == ph_work2 else 'false'
            work = gdata.data.PhoneNumber(text=ph_work2,
                                          primary=prim,
                                          rel=gdata.data.WORK_REL)
            new_contact.phone_number.append(work)

        if ph_other and self.is_valid_phone_number(ph_other, 'Other', name):
            prim  = 'true' if ph_prim == ph_other else 'false'
            other = gdata.data.PhoneNumber(text=ph_other,
                                           primary=prim,
                                           rel=gdata.data.OTHER_REL)
            new_contact.phone_number.append(other)

        if fax_home and self.is_valid_phone_number(ph_fax, 'Fax Home', name):
            prim = 'true' if fax_prim == fax_home else 'false'
            home = gdata.data.PhoneNumber(text=fax_home,
                                          primary=prim,
                                          rel=gdata.data.HOME_FAX_REL)
            new_contact.phone_number.append(home)

        if fax_work and self.is_valid_phone_number(fax_work, 'Fax Work', name):
            prim = 'true' if fax_prim == fax_work else 'false'
            work = gdata.data.PhoneNumber(text=fax_work,
                                          primary=prim,
                                          rel=gdata.data.WORK_FAX_REL)
            new_contact.phone_number.append(work)

        if nickname:
            nickname = gdata.contacts.data.NickName(text=nickname)
            new_contact.nickname = nickname

        if gender:
            gender = gdata.data.Gender(value=gender)
            new_contact.gender = gender

        if birthday:
            dt = utils.pytime_to_yyyy_mm_dd(birthday)
            bday = gdata.contacts.data.Birthday(when=dt)
            new_contact.birthday = bday

        if anniv:
            dt = utils.pytime_to_yyyy_mm_dd(anniv)
            date = gdata.data.When(start=dt)
            ann  = gdata.contacts.data.Event(when=date, rel='anniversary')
            new_contact.event.append(ann)

        # Outlook has no concept of a primary website address: there ae
        # only two addresses. We will assume that if a personal website
        # is available it is primary, even if a work website is
        # available
        if web_home:
            prim = 'true'
            home = gdata.contacts.data.Website(href=web_home,
                                               primary=prim,
                                               rel='home-page')
            new_contact.website.append(home)

        if web_work:
            prim = 'true' if not web_home else 'false'
            w    = gdata.contacts.data.Website(href=web_work,
                                               primary=prim,
                                               rel='work')
            new_contact.website.append(w)

        return new_contact


    def create_contact_on_server (self, new_contact):
        entry = self.gd_client.CreateContact(new_contact)
    
        if entry:
            logging.debug('Creation Successful!')
            logging.debug('ID for the new contact: %s', entry.id.text)
        else:
            logging.error('Contact creation error.')

        return entry


    def create_contact (self, entryid, name, gnames, emails=None, 
                        gids=None, company=None, notes=None,
                        title=None, dept=None, ph_prim=None, postal=None,
                        ph_mobile=None, ph_home=None, ph_work=None,
                        ph_home2=None, ph_work2=None, ph_other=None,
                        fax_home=None, fax_work=None,
                        birthday=None,    anniv=None,
                        nickname=None, gender=None,
                        web_home=None, web_work=None,
                        gcid=None):
        """Create a contact with provided information.
    
        If gids - an array of Group IDs - is specified, then the created
        contact is attached to each group in that array. If gids is
        None, but a corresponding array of group names is provided, then
        the contact is added to those groups. If any group in the
        provided group name array is not found, it is created first.
    
        'emails' is an array of addresses. If there is more than one
        element in this array, the first element is marked as the
        primary email address.
        """
    
        new_con = self.create_contact_entry(entryid, name, gnames,
                                            emails, gids, company,
                                            notes, title, dept, ph_prim,
                                            postal, ph_mobile, ph_home,
                                            ph_work, ph_work2, ph_home2,
                                            fax_home, fax_work, fax_prim,
                                            birthday, anniv, nickname,
                                            gender, web_home, web_work,
                                            ph_other, gcid)
  
        entry = self.create_contact_on_server(new_con)
    
        return entry


    def add_olid_to_ce (self, ce, olid, replace=True):
        """Insert the Outlook EntryID for a contact as a  userdefined property
        in the Google ContactEntry and returned the modified ContactEntry.
        
        olid is the values as returned by GetProps - and, as a result a binary
        value. We base64 encode it before inserting into ContactEntry.

        If replace is True, then the first existing olid entry (if any) will
        be replaced with teh provided value. If it is False, then it is
        appended to existing list."""

        entryid_b64 = base64.b64encode(olid)
        ud       = gdata.contacts.data.UserDefinedField()
        ud.key   = 'olid'
        ud.value = entryid_b64

        if replace and len(ce.user_defined_field) > 0:
            ce.user_defined_field.pop()

        ce.user_defined_field.append(ud)

        return ce

    def new_feed (self):
        return gdata.contacts.data.ContactsFeed()


    def _get_group_feed (self, gid):
        query             = gdata.contacts.client.ContactsQuery()
        query.max_results = 100000
        query.showdeleted = 'false'
        query.group       = gid
        
        feed = self.gd_client.GetContacts(q=query)
        return feed

    def _get_updated_gc_feed (self, updated_min, gid):
        query             = gdata.contacts.client.ContactsQuery()
        query.max_results = 100000
        query.updated_min = updated_min
        query.showdeleted = 'true'
        query.group       = gid

        feed = self.gd_client.GetContacts(q=query)
        return feed


    def del_dict_items (self, d, l, keys=True):
        """Delete all the elements in d that match the elements in list
        l. If 'keys' is True the match is done on the keys of d, else
        match is done on the values of d"""
        
        # Don't you love python - all the compactness of Perl less all
        # the chaos

        if keys:
            d = dict([(x,y) for x,y in d.iteritems() if not x in l])
        else:
            d = dict([(x,y) for x,y in d.iteritems() if not y in l])

        return d

    def del_con_mod_by_values (self, ary):
        """Remove all entries in thr con_mod dictionary whose values
        appear in the 'ary' list."""

        self.con_gc_mod = self.del_dict_items(self.con_gc_mod,
                                              ary, False)

    def reset_sync_lists (self):
        """In these structures, all olids are base64 encoded."""
        self.con_all    = {}
        self.con_gc_del = {}
        self.con_gc_mod = {}
        self.con_gc_new = []

    def get_con_new (self):
        return self.con_gc_new

    def get_con_mod (self):
        return self.con_gc_mod

    def prep_gc_contact_lists (self, cnt=0):
        logging.info('Querying Google for status of Contact Entries...')

        updated_min = self.config.get_last_sync_stop()
        gid         = self.config.get_gid()
        feed = self._get_updated_gc_feed(updated_min, gid)

        logging.info('Response recieved from Google. Processing...')

        self.reset_sync_lists()

        if not feed.entry:
            logging.info('No entries in feed.')
            return

        skip = 0

        for i, entry in enumerate(feed.entry):
            gcid = utils.get_link_rel(entry.link, 'edit')
            olid = get_udp_by_key(entry.user_defined_field, 'olid')
            epd  = entry.deleted

            if epd:
                if olid:
                    self.con_gc_del[gcid] = olid
                else:
                    # Deleted before it got synched. Get on with life
                    skip += 1
                    continue
            else:
                if olid:
                    self.con_gc_mod[gcid] = olid
                else:
                    self.con_gc_new.append(gcid)

        logging.debug('==== GC =====')
        logging.debug('num processed    : %5d', i+1)
        logging.debug('num total        : %5d', len(self.con_all.items()))
        logging.debug('num new          : %5d', len(self.con_gc_new))
        logging.debug('num mod          : %5d', len(self.con_gc_mod))
        logging.debug('num del          : %5d', len(self.con_gc_del))
        logging.debug('num del bef sync : %5d', skip)

    def exec_batch (self, batch_feed):
        return self.gd_client.ExecuteBatch(
            batch_feed, gdata.contacts.client.DEFAULT_BATCH_URL)


def main():
    config = Config('app_state.json')
    gn     = config.get_gn()
    gid    = config.get_gid()
    
    # Parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], '', ['user=', 'pw='])
    except getopt.error, msg:
        print 'python gc_wrapper.py --user [username] --pw [password]'
        sys.exit(2)
  
    user = ''
    pw = ''
    # Process options
    for option, arg in opts:
        if option == '--user':
            user = arg
        elif option == '--pw':
            pw = arg
  
    while not user:
        user = raw_input('Please enter your username: ')

    while not pw:
        pw = getpass.getpass()
        if not pw:
            print 'Password cannot be blank.'

    try:
        sample = GC(config, user, pw)
    except gdata.client.BadAuthentication:
        print 'Invalid user credentials given.'
        return
  
#  sample.create_group('Karra Sync')
    sample.find_group(gn)
    sample.prep_gc_contact_lists()
#  sample.print_groups()
#    sample.create_contact('Entry Id: 2', 'Good Fellow Bolly',
#                         ['bolly@goodfellow.com'],
#                          'This is one fellow who is really bolly & gay',
#                           gnames=[gn])


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()
