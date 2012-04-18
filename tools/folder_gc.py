##
## Created       : Wed May 18 13:16:17 IST 2011
## Last Modified : Wed Apr 18 14:00:58 IST 2012
##
## Copyright (C) 2011, 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
## 

import logging, os, re, sys, traceback
from   abc            import ABCMeta, abstractmethod
from   folder         import Folder
from   contact_gc     import GCContact

import utils
import atom, gdata.contacts.client

def get_udp_by_key (udps, key):
    """Get the first User Defined Property from the given list that has the
    specified key"""

    for ep in udps:
        if ep.key == key:
            if ep.value:
                return ep.value
            else:
                value = 'Hrrmph. '
                print 'Value: ', value

    return None

def get_udps_by_key_prefix (udps, keyprefix):
    """Get a dictionary of all the user defind properties whose keys have a
    prefix match with the specified string"""

    ret = {}
    for ep in udps:
        if re.search(('^' + keyprefix), ep.key):
            if ep.value:
                ret.update({ep.key : ep.value})
            else:
                value = 'Hrrmph. '
                print 'Value: ', value

    return ret

def sync_status_str (const):
    for name, val in globals().iteritems():
        if name[:5] == 'SYNC_' and val == const:
            return name

    return None

SYNC_OK                    = 200
SYNC_CREATED               = 201
SYNC_NOT_MODIFIED          = 304
SYNC_BAD_REQUEST           = 400
SYNC_UNAUTHORIZED          = 401
SYNC_FORBIDDEN             = 403
SYNC_CONFLICT              = 409
SYNC_INTERNAL_SERVER_ERROR = 500

## Unlike the Outlook case, we will avoid doing another level of abstract
## class. When we get to implementing the tasks stuff we can evolve the class
## structure as well. for now, taking the easy way out

class GCContactsFolder(Folder):
    """A GC Folder directly corresponds to a Contacts Group or a Calendar, for
    e.g. This itself will be an abstract class that implements some of the
    abstract methods, but the real final leaf classes will be the Google
    Contacts and Google Tasks classes"""

    #    __metaclass__ = ABCMeta

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

    def get_batch_size (self):
        return 100

    def prep_sync_lists (self, destid, sl, updated_min=None, cnt=0):
        """See the documentation in folder.Folder"""

        pname = sl.get_pname()
        conf  = self.get_config()

        logging.info('Querying Google for status of Contact Entries...')
        stag = conf.make_sync_label(pname, destid)

        ## Sort the DBIds so dest1 has the 'lower' ID
        db1 = self.get_db().get_dbid()
        if db1 > destid:
            db2 = db1
            db1 = destid
        else:
            db2 = destid

        if not updated_min:
            updated_min = conf.get_last_sync_stop(pname)

        feed = self._get_group_feed(updated_min=updated_min, showdeleted='false')

        logging.info('Response recieved from Google. Processing...')

        if not feed.entry:
            logging.info('No entries in feed.')
            return

        skip     = 0
        etag_cnt = 0

        for i, entry in enumerate(feed.entry):
            gcid = utils.get_link_rel(entry.link, 'edit')
            olid = get_udp_by_key(entry.user_defined_field, stag)
            etag = entry.etag
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

            if etag:
                sl.add_etag(gcid, etag)
                etag_cnt += 1
            else:
                sl.add_entry(gcid)

        logging.debug('==== GC =====')
        logging.debug('num processed    : %5d', i+1)
        logging.debug('num total        : %5d', len(sl.get_entries()))
        logging.debug('num with etags   : %5d', etag_cnt)
        logging.debug('num new          : %5d', len(sl.get_news()))
        logging.debug('num mod          : %5d', len(sl.get_mods()))
        logging.debug('num del          : %5d', len(sl.get_dels()))
        logging.debug('num del bef sync : %5d', skip)

        return (sl.get_news(), sl.get_mods(), sl.get_dels())

    def find_item (self, itemid):
        gce = self.get_gdc().GetContact(itemid)
        gc  = GCContact(self, gce=gce)

        return gc

    def find_items (self, itemids):
        """See documentation in folder.Folder"""
        
        ## Note that it is more efficient to do a single call to fetch all the
        ## entire and then build GCContact objects, than call find_item
        ## iteratively...
        ces = self._fetch_gc_entries(itemids)
        ret = [GCContact(self, gce=ce) for ce in ces]

        return ret

    def batch_create (self, src_sl, src_dbid, items):
        """See the documentation in folder.Folder"""

        my_dbid = self.get_dbid()
        c       = self.get_config()
        src_sync_tag = c.make_sync_label(src_sl.get_pname(), src_dbid)
        dst_sync_tag = c.make_sync_label(src_sl.get_pname(), my_dbid)

        f     = self.get_db().new_feed()
        stats = BatchState(1, f, 'insert', sync_tag=dst_sync_tag)

        for item in items:
            gc  = GCContact(self, con=item)
            bid = item.get_itemid()
            gc.update_sync_tags(src_sync_tag, bid)

            gce = gc.get_gce()

            stats.add_con(bid, new=gc, orig=item)
            f.add_insert(entry=gce, batch_id_string=bid)
            stats.incr_cnt()
            
            if stats.get_cnt() % self.get_batch_size() == 0:
                # Feeds have to be less than 1MB. We can push this some
                # more. FIXME.
                logging.debug('Uploading new batch # %02d to Google. ' +
                              'Count: %3d. Size: %6.2fK',
                              stats.get_bnum(), stats.get_cnt(),
                              stats.get_size())
                rf = self.get_db().exec_batch(f)
                stats.process_batch_response(rf)

                f = self.get_db().new_feed()
                stats = BatchState(stats.get_bnum()+1, f, 'insert',
                                   sync_tag=dst_sync_tag)
           
        # Upload any leftovers
        if stats.get_cnt() > 0:
            logging.debug('New Batch # %02d. Count: %3d. Size: %5.2fK',
                          stats.get_bnum(), stats.get_cnt(),
                          stats.get_size())
            rf = self.get_db().exec_batch(f)
            stats.process_batch_response(rf)

    def _fetch_gc_entries (self, gcids):
        """gcids is a list of google contact ids to retrieve contact
        entries for.

        Returns a list of ContactEntries"""

        f      = self.get_db().new_feed()
        stats = BatchState(1, f, 'query', sync_tag=None)

        ret = []

        for gcid in gcids:
            ce = gdata.contacts.data.ContactEntry()
            ce.id = atom.data.Id(text=gcid)
            stats.add_con(gcid, ce, orig=None)

            f.add_query(entry=ce, batch_id_string=gcid)
            stats.incr_cnt()

            if stats.get_cnt() % self.get_batch_size() == 0:
                # Feeds have to be less than 1MB. We can push this some
                # more
                logging.debug('Qry Batch # %02d. Count: %3d. Size: %6.2fK',
                              stats.get_bnum(), stats.get_cnt(),
                              stats.get_size())

                rf  = self.get_db().exec_batch(f)
                ces = stats.process_batch_response(rf)
                [ret.append(x) for x in ces]

                f = self.get_db().new_feed()
                s = BatchState(stats.get_bnum()+1, f, 'query', sync_tag=None)
                stats = s

        # Process any leftovers
        if stats.get_cnt() > 0:
            logging.debug('Qry Batch # %02d. Count: %3d. Size: %5.2fK',
                          stats.get_bnum(), stats.get_cnt(),
                          stats.get_size())
            
            rf  = self.get_db().exec_batch(f)
            ces = stats.process_batch_response(rf)
            [ret.append(x) for x in ces]

        return ret

    def batch_update (self, sync_list, src_dbid, items):
        """See the documentation in folder.Folder"""

        # Updates and deletes on google require not just the entryid but also
        # its correct etag which is a version identifier. This is to ensure
        # two apps do not overwrite each other's work without even knowing
        # about it. So we need to approach this in two steps: (a) Fetch the
        # ContactEntries for all the items we are interested in. the returned
        # entry objects have all the required info, including the latest
        # etag. (b) Modify the same entry with the local updates and send it
        # back

        gcids = [item.get_sync_tags('asynk:gc:id') for item in items]
        logging.debug('Refreshing etags for modified entries...')
        ces   = self._fetch_gc_entries(gcids)
        etags = [ce.etag for ce in ces]

        my_dbid = self.get_dbid()
        c       = self.get_config()
        pname   = sync_list.get_pname()

        src_sync_tag = c.make_sync_label(pname, src_dbid)
        dst_sync_tag = c.make_sync_label(pname, my_dbid)

        f     = self.get_db().new_feed()
        stats = BatchState(1, f, 'update', sync_tag=dst_sync_tag)

        for item, etag in zip(items, etags):
            gc  = GCContact(self, con=item)
            bid = item.get_itemid()
            gc.update_sync_tags(src_sync_tag, bid)

            gce = gc.get_gce()
            gce.etag = etag

            stats.add_con(bid, new=gc, orig=item)
            f.add_update(entry=gce, batch_id_string=bid)
            stats.incr_cnt()
            
            if stats.get_cnt() % self.get_batch_size() == 0:
                # Feeds have to be less than 1MB. We can push this some
                # more. FIXME.
                logging.debug('Uploading mod batch # %02d to Google. ' +
                              'Count: %3d. Size: %6.2fK',
                              stats.get_bnum(), stats.get_cnt(),
                              stats.get_size())
                rf = self.get_db().exec_batch(f)
                stats.process_batch_response(rf)

                f = self.get_db().new_feed()
                stats = BatchState(stats.get_bnum()+1, f, 'update',
                                   sync_tag=dst_sync_tag)
           
        # Upload any leftovers
        if stats.get_cnt() > 0:
            logging.debug('Mod Batch # %02d. Count: %3d. Size: %5.2fK',
                          stats.get_bnum(), stats.get_cnt(),
                          stats.get_size())
            rf = self.get_db().exec_batch(f)
            stats.process_batch_response(rf)

    def writeback_sync_tags (self, items):
        ## FIXME: fix the hardcoding below
        stag  = 'asynk:ol:id'
        f     = self.get_db().new_feed()
        stats = BatchState(1, f, 'Writeback olid', sync_tag=stag)

        for item in items:
            etag = item.get_etag()
            if not etag:
                logging.error('GC (%s: %s) is expected to have a etag.',
                              item.get_name(), item.get_itemid())
                continue

            iid = item.get_sync_tags(stag)
            gce = item.get_gce()

            stats.add_con(iid, new=gce, orig=item)
            f.add_update(entry=gce, batch_id_string=iid)
            stats.incr_cnt()
            
            if stats.get_cnt() % self.get_batch_size() == 0:
                # Feeds have to be less than 1MB. We can push this some
                # more. FIXME.
                logging.info('Uploading Oulook EntryIDs to Google...')
                logging.debug('Batch #%02d. Count: %3d. Size: %6.2fK',
                              stats.get_bnum(), stats.get_cnt(),
                              stats.get_size())

                rf = self.get_db().exec_batch(f)
                stats.process_batch_response(rf)

                f = self.get_db().new_feed()
                stats = BatchState(stats.get_bnum()+1, f, 'Writeback olid',
                                   sync_tag=dst_sync_tag)
           
        # Upload any leftovers
        if stats.get_cnt() > 0:
            logging.info('Uploading Oulook EntryIDs to Google...')
            logging.debug('Batch # %02d. Count: %3d. Size: %5.2fK',
                          stats.get_bnum(), stats.get_cnt(),
                          stats.get_size())

            rf = self.get_db().exec_batch(f)
            stats.process_batch_response(rf)                

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

class BatchState:
    """This class is used as a temporary store of state related to batch
    operations in the Google API. Useful when we are operating in bulk data
    on Google"""

    def __init__ (self, num, f, op=None, sync_tag=None):
        self.size = 0
        self.cnt  = 0
        self.num  = num
        self.f    = f
        self.operation = op
        self.cons = {}
        self.origs = {}
        self.sync_tag = sync_tag

    def get_size (self):
        """Return size of feed in kilobytess."""
        self.size = len(str(self.f))/1024.0
        return self.size

    def incr_cnt (self):
        self.cnt += 1
        return self.cnt

    def get_cnt (self):
        return self.cnt

    def get_bnum (self):
        return self.num

    def add_con (self, olid_b64, new, orig):
        self.cons[olid_b64] = new
        self.origs[olid_b64] = orig

    def get_con (self, olid_b64):
        return self.cons[olid_b64]

    def get_orig (self, olid_b64):
        return self.origs[olid_b64]

    def get_operation (self):
        return self.operation

    def set_operation (self, op):
        self.operation = op

    def process_batch_response (self, resp):
        """resp is the response feed obtained from a batch operation to
        google.
    
        This routine will walk through the batch response entries, and
        make note in the outlook database for succesful sync, or handle
        errors appropriately."""
    
        op   = self.get_operation()
        cons = []
    
        for entry in resp.entry:
            bid    = entry.batch_id.text if entry.batch_id else None
            if not entry.batch_status:
                # There is something seriously wrong with this request.
                logging.error('Unknown fatal error in response. Full resp: %s',
                              entry)
                continue
    
            code   = int(entry.batch_status.code)
            reason = entry.batch_status.reason
    
            if code != SYNC_OK and code != SYNC_CREATED:
                # FIXME this code path needs to be tested properly
                err = sync_status_str(code)
                err_str = '' if err is None else ('Code: %s' % err)
                err_str = 'Reason: %s. %s' % (reason, err_str)
    
                if op == 'insert' or op == 'update':
                    try:
                        name = self.get_con(bid).name
                    except Exception, e:
                        name = self.get_con(bid).get_name()
                    except Exception, e:
                        name = "WTH!"    

                    logging.error('Upload to Google failed for: %s: %s',
                                  name, err_str)
                elif op == 'Writeback olid':
                    logging.error('Could not complete sync for: %s: %s',
                                  self.get_con(bid).name, err_str)
                else:
                    ## We could just print a more detailed error for all
                    ## cases. Should do some time FIXME.
                    logging.error('Sync failed for bid %s: %s',
                                   bid, err_str)
            else:
                if op == 'query':
                    con = entry
                    # We could build and return array for all cases, but
                    # why waste memory...
                    cons.append(con)
                else:
                    con  = self.get_con(bid)
                    orig = self.get_orig(bid)
                    gcid = utils.get_link_rel(entry.link, 'edit')
                    orig.update_sync_tags(self.sync_tag, gcid)
                    cons.append(orig)

                    t = None
                    if op == 'insert':
                        t = 'created'
                    elif op == 'update':
                        t = 'updated'
    
                    if t:
                        logging.info('Successfully %s gmail entry for %30s (%s)',
                                     t, con.get_name(), orig.get_itemid())
    
        return cons
