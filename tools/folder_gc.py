##
## Created       : Wed May 18 13:16:17 IST 2011
## Last Modified : Tue Mar 20 16:26:20 IST 2012
##
## Copyright (C) 2011, 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
## 

import sys, os, logging, traceback
from   abc            import ABCMeta, abstractmethod
from   folder         import Folder
import gdata.contacts.client

## Unlike the Outlook case, we will avoid doing another level of abstract
## class. When we get to implementing the tasks stuff we can evolve the class
## structure as well. for now, taking the easy way out

class GCContactsFolder(Folder):
    """A GC Folder directly corresponds to a Contacts Group or a Calendar, for
    e.g. This itself will be an abstract class that implements some of the
    abstract methods, but the real final leaf classes will be the Google
    Contacts and Google Tasks classes"""

    __metaclass__ = ABCMeta

    def __init__ (self, db, gid, gn, gcentry):
        Folder.__init__(self, db)

        self.set_itemid(gid)
        self.set_name(gn)
        self.set_gcentry(gcentry)
        self.set_type(Folder.CONTACT_t)
        self.set_gdc(db.get_gdc())

    ##
    ## Implementation of the abstract methods inherited from Folder
    ##

    def prep_sync_lists (self, destid, last_sync_stop, limit=0):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def insert_new_items (self, items):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def bulk_clear_sync_flags (self, dbids):
        """See the documentation in folder.Folder"""

        ## FIXME: Need to revisit this method once we get to the sync
        ## stage. The following code actually gets rid of the entire
        ## group. This routine should only clear the sync flags from the
        ## individual entries like in the Outlook case where the property tags
        ## are removed, making them look like unsynched entries

        self.del_all_entries()
       
    def __str__ (self):
        ret = 'Contacts'

        return ('%s.\tName: %s;\tGID: %s;\t' % (ret, self.get_name(),
                                                self.get_itemid()))

    ##
    ## Internal and helper routines
    ##

    def get_gdc (self):
        return self._get_prop('gdc')

    def set_gdc (self, gdc):
        self._set_prop('gdc', gdc)

    def get_gcentry (self):
        return self._get_prop('gcentry')

    def set_gcentry (self, gcentry):
        self._set_prop('gcentry', gcentry)

    def _get_group_feed (self):
        query             = gdata.contacts.client.ContactsQuery()
        query.max_results = 100000
        query.showdeleted = 'false'
        query.group       = self.get_itemid()
        
        feed = self.get_gdc().GetContacts(q=query)
        return feed

    def del_all_entries (self):
        """Delete all contacts in specified group. """

        feed = self._get_group_feed()

        # A batch operation would be much faster... should implement
        # someday
        for con in feed.entry:
            logging.info('Deleting ID: %s; Name: %s...', con.id.text,
                         con.name.full_name.text if con.name else '')
            self.get_gdc().Delete(con)
  
    ## Temporarily placing keeping this stuff here while we start by cleaning
    ## up pimdb_gc.py

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
