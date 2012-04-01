##
## Created       : Wed May 18 13:16:17 IST 2011
## Last Modified : Sun Apr 01 16:23:37 IST 2012
##
## Copyright (C) 2011, 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
## 

import sys, os, logging, traceback
from   abc            import ABCMeta, abstractmethod
from   folder         import Folder
import utils
import gdata.contacts.client

def get_udp_by_key (udps, key):

    for ep in udps:
        if ep.key == key:
            if ep.value:
                return ep.value
            else:
                value = 'Hrrmph. '
                print 'Value: ', value

    return None

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

    def prep_sync_lists (self, destid, sl, updated_min=None, cnt=0):
        """See the documentation in folder.Folder"""

        logging.info('Querying Google for status of Contact Entries...')

        ## Sort the DBIds so dest1 has the 'lower' ID
        db1 = self.get_db().get_dbid()
        if db1 > destid:
            db2 = db11
            db1 = destid
        else:
            db2 = destid

        if not updated_min:
            updated_min = self.get_config().get_last_sync_stop(db1, db2)

        feed = self._get_group_feed(updated_min=updated_min, showdeleted='false')

        logging.info('Response recieved from Google. Processing...')

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
                    sl.add_del(gcid, olid)
                else:
                    # Deleted before it got synched. Get on with life
                    skip += 1
                    continue
            else:
                if olid:
                    sl.add_mod(gcid, olid)
                else:
                    sl.add_new(gcid)

        logging.debug('==== GC =====')
        logging.debug('num processed    : %5d', i+1)
        logging.debug('num total        : %5d', len(sl.get_all().items()))
        logging.debug('num new          : %5d', len(sl.get_news()))
        logging.debug('num mod          : %5d', len(sl.get_mods()))
        logging.debug('num del          : %5d', len(sl.get_dels()))
        logging.debug('num del bef sync : %5d', skip)

        return (sl.get_news(), sl.get_mods(), sl.get_dels())

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

    def _get_group_feed (self, showdeleted='false', updated_min=None):
        query             = gdata.contacts.client.ContactsQuery()
        query.max_results = 100000
        query.showdeleted = showdeleted
        query.group       = self.get_itemid()

        if updated_min:
            query.updated_min = updated_min
        
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
