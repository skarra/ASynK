#!/usr/bin/python
## 
## gc_wrapper.py
##  
## Created       : Thu Jul 07 14:47:54  2011
## Last Modified : Mon Jul 11 14:42:20  2011
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

gid = 'http://www.google.com/m8/feeds/groups/karra.etc%40gmail.com/base/5353d42d8d17504a'
gns  = ['Karra Sync']

class GC (object):
  """GC object is a wrapper for a Google Contacts stream API."""

  def __init__(self, email, password):
    """Constructor for the GC wrapper object.
    
    Takes an email and password corresponding to a gmail account, and
    can do various things to the contact list such as upload, and
    modify, etc.
    """

    self.gd_client = gdata.contacts.client.ContactsClient(source='Outlook-Android-Contacts-Sync')
    self.gd_client.ClientLogin(email, password, self.gd_client.source)

  def get_groups (self):
    feed = self.gd_client.GetGroups()
    return feed

  def print_groups (self):
      feed = self.get_groups()

      if not feed.entry:
          print '\nNo groups in feed.\n'
          return 0
      for i, entry in enumerate(feed.entry):
          print '\n%s %s' % (i+1, entry.title.text)
          if entry.content:
              print '  Yeah: %s' % (entry.content.text)
          # Display the group id which can be used to query the contacts
          # feed.
          print '  Group ID: %s' % entry.id.text

          # Display extended properties.
          for extended_property in entry.extended_property:
              if extended_property.value:
                  value = extended_property.value
              else:
                  value = extended_property.GetXmlBlob()
                  print '  Extended Property %s: %s' % (extended_property.name, value)
      return len(feed.entry)


  def clear_group (self, gid):
    """Delete all contacts in specified group
    """
    pass

  def find_group (self, title):
    """Find the group with the given name.

    Takes a group title, and returns the Group ID if found. Returns None
    if the group cannot be found.
    """

    feed = self.gd_client.GetGroups()

    if not feed.entry:
      logging.debug('\nGroup (%s) not found: there are no groups!',
                    title)
      return None

    for i, entry in enumerate(feed.entry):
      if entry.title.text == title:
        logging.debug('Group (%s) found. ID: %s',
                      title, entry.id.text)
        return entry.id.text

    logging.debug('\nGroup (%s) not found in group list.!',
                  title)
    return None

  def create_group (self, title='Default News'):
    gn = gdata.data.Name(name=title)
    new_group = gdata.contacts.data.GroupEntry(name=gn)
    new_group.title = atom.data.Title(text=title)

    entry = self.gd_client.create_group(new_group)

    if entry:
      logging.debug('Successfully created group!')
      logging.debug('ID for the new group: %s', entry.id.text)
      return entry.id.text
    else:
      logging.error('Group creation error.')
      return None


  def create_contact (self, entryid, name, emails=None, notes=None,
                      gnames=gns, gids=None, company=None,
                      title=None, dept=None, ph_prim=None, postal=None,
                      ph_mobile=None, ph_home=None, ph_work=None):
    """Create a contact with provided information.

    If gids - an array of Group IDs - is specified, then the created
    contact is attached to each group in that array. If gids is None,
    but a corresponding array of group names is provided, then the
    contact is added to those groups. If any group in the provided group
    name array is not found, it is created first.

    'emails' is an array of addresses. If there is more than one element
    in this array, the first element is marked as the primary email
    address.
    """

    if not gids:
      gids = []
      for gname in gnames:
        gid = self.find_group(gname)

        if not gid:
          gid = self.create_group(gname)

        gids.append(gid)

    fn = gdata.data.FullName(text=name)
    n  = gdata.data.Name(full_name=fn)

    # First create a bare bones contact structure. We will populate the
    # fields as we go along

    new_contact = gdata.contacts.data.ContactEntry(name=n)
    new_contact.content = atom.data.Content(text=notes)

    # Set up the group memberships
    for gid in gids:
      gidm = gdata.contacts.data.GroupMembershipInfo(href=gid)
      new_contact.group_membership_info.append(gidm)

    # Populate the email addresses
    if emails:
      # Create a work email address for the contact and use as primary.
      i = 0
      for email in emails:
        prim = 'true'
        if i > 0:
          prim = 'false'

        em = gdata.data.Email(address=email, primary=prim,
                              rel=gdata.data.WORK_REL)
        new_contact.email.append(em)
        i += 1

    # Populate the postal address. We need to extract out the relevant
    # bits and populate in a structured fashion. For now dump the entire
    # thing into the 'street' component.
    if postal:
      strt = gdata.data.Street(text=postal)
      add = gdata.data.StructuredPostalAddress(street=strt,
                                               primary='true',
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
    if ph_mobile:
      prim = 'true' if ph_prim == ph_mobile else 'false'
      mobile = gdata.data.PhoneNumber(text=ph_mobile,
                                      primary=prim,
                                      rel=gdata.data.MOBILE_REL)
      new_contact.phone_number.append(mobile)

    if ph_home:
      prim = 'trie' if ph_prim == ph_home else 'false'
      home = gdata.data.PhoneNumber(text=ph_home,
                                    primary=prim,
                                    rel=gdata.data.HOME_REL)
      new_contact.phone_number.append(home)

    if ph_work:
      prim = 'true' if ph_prim == ph_work else 'false'
      work = gdata.data.PhoneNumber(text=ph_work,
                                    primary=prim,
                                    rel=gdata.data.WORK_REL)
      new_contact.phone_number.append(work)
      

    # Finally, make a request to the server to create the contact
    entry = self.gd_client.CreateContact(new_contact)

    if entry:
      logging.debug('Creation Successful!')
      logging.debug('ID for the new contact: %s', entry.id.text)
    else:
      logging.error('Contact creation error.')


def main():
  global gid, gn
  
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
      sample = GC(user, pw)
  except gdata.client.BadAuthentication:
      print 'Invalid user credentials given.'
      return

#  sample.create_group('Karra Sync')
#  sample.find_group(gn)
#  sample.print_groups()
  sample.create_contact('Entry Id: 2', 'Good Fellow Bolly',
                        ['bolly@goodfellow.com'],
                        'This is one fellow who is really bolly & gay',
                         gnames=gns)


if __name__ == '__main__':
  logging.getLogger().setLevel(logging.DEBUG)
  main()
