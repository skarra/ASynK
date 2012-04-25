##
## Created       : Wed May 18 13:16:17 IST 2011
## Last Modified : Wed Apr 25 16:12:59 IST 2012
##
## Copyright (C) 2011, 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
## 

import copy, logging, os, re, sys, traceback
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

        self.reset_contacts()

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

    def new_item (self, item):
        """Add the specified item to the folder."""

        if item.__class__.__name__ == 'GCContact':
            con = item
        else:
            con = GCContact(self, con=item)

        eid = con.save()
        return eid

    def find_item (self, itemid):
        gce = self.get_gdc().GetContact(itemid)
        gc  = GCContact(self, gce=gce)

        return gc

    def find_items (self, itemids):
        """See documentation in folder.Folder"""
        
        ## Note that it is more efficient to do a single call to fetch all the
        ## entire and then build GCContact objects, than call find_item
        ## iteratively...
        res, ces = self._fetch_gc_entries(itemids)
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

        success = True
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
                succ, cons = stats.process_batch_response(rf)
                success = success and succ

                f = self.get_db().new_feed()
                stats = BatchState(stats.get_bnum()+1, f, 'insert',
                                   sync_tag=dst_sync_tag)
           
        # Upload any leftovers
        if stats.get_cnt() > 0:
            logging.debug('New Batch # %02d. Count: %3d. Size: %5.2fK',
                          stats.get_bnum(), stats.get_cnt(),
                          stats.get_size())
            rf = self.get_db().exec_batch(f)
            succ, cons = stats.process_batch_response(rf)
            success = success and succ

        return success

    def _fetch_gc_entries (self, gcids):
        """gcids is a list of google contact ids to retrieve contact
        entries for.

        Returns a list of ContactEntries"""

        f      = self.get_db().new_feed()
        stats = BatchState(1, f, 'query', sync_tag=None)

        ret = []
        success = True

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
                suc, ces = stats.process_batch_response(rf)
                success = success and suc
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
            suc, ces = stats.process_batch_response(rf)
            success = success and suc
            [ret.append(x) for x in ces]

        return success, ret

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

        my_dbid = self.get_dbid()
        c       = self.get_config()
        pname   = sync_list.get_pname()

        src_sync_tag = c.make_sync_label(pname, src_dbid)
        dst_sync_tag = c.make_sync_label(pname, my_dbid)

        tags  = [item.get_sync_tags(dst_sync_tag)[0] for item in items]
        gcids = [val for (tag, val) in tags]

        logging.debug('Refreshing etags for modified entries...')

        success, ces   = self._fetch_gc_entries(gcids)
        etags = [copy.deepcopy(ce.etag) for ce in ces]
        f     = self.get_db().new_feed()
        stats = BatchState(1, f, 'update', sync_tag=dst_sync_tag)

        for item, etag in zip(items, etags):
            gc  = GCContact(self, con=item)
            bid = item.get_itemid()
            gc.update_sync_tags(src_sync_tag, bid)

            gce = gc.get_gce()
            gce.etag = etag

            logging.debug('Sending gce: %s', str(gce))

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
                succ, cons = stats.process_batch_response(rf)
                success = success and succ

                f = self.get_db().new_feed()
                stats = BatchState(stats.get_bnum()+1, f, 'update',
                                   sync_tag=dst_sync_tag)
           
        # Upload any leftovers
        if stats.get_cnt() > 0:
            logging.debug('Mod Batch # %02d. Count: %3d. Size: %5.2fK',
                          stats.get_bnum(), stats.get_cnt(),
                          stats.get_size())
            rf = self.get_db().exec_batch(f)
            succ, cons = stats.process_batch_response(rf)
            success = success and succ

        return success

    def writeback_sync_tags (self, pname, items):
        conf  = self.get_config()
        remid = conf.get_other_dbid(pname, self.get_dbid())
        stag  = conf.make_sync_label(pname, remid)

        f     = self.get_db().new_feed()
        stats = BatchState(1, f, 'Writeback olid', sync_tag=stag)

        for item in items:
            etag = item.get_etag()
            if not etag:
                logging.error('GC (%s: %s) is expected to have a etag.',
                              item.get_name(), item.get_itemid())
                continue

            tags = item.get_sync_tags(stag)
            if not tags:
                logging.debug('Null tags. Item: \n%s', item)
                raise Exception()

            t, iid = tags[0]
            gce = item.get_gce(refresh=True)

            stats.add_con(iid, new=gce, orig=item)
            f.add_update(entry=gce, batch_id_string=iid)
            stats.incr_cnt()
            
            if stats.get_cnt() % self.get_batch_size() == 0:
                # Feeds have to be less than 1MB. We can push this some
                # more. FIXME.
                logging.info('Uploading Remote ItemIDs to Google...')
                logging.debug('Batch #%02d. Count: %3d. Size: %6.2fK',
                              stats.get_bnum(), stats.get_cnt(),
                              stats.get_size())

                rf = self.get_db().exec_batch(f)
                stats.process_batch_response(rf)

                f = self.get_db().new_feed()
                stats = BatchState(stats.get_bnum()+1, f, 'Writeback olid',
                                   sync_tag=stag)
           
        # Upload any leftovers
        if stats.get_cnt() > 0:
            logging.info('Uploading Remote ItemIDs to Google...')
            logging.debug('Batch # %02d. Count: %3d. Size: %5.2fK',
                          stats.get_bnum(), stats.get_cnt(),
                          stats.get_size())

            rf = self.get_db().exec_batch(f)
            stats.process_batch_response(rf)                

    def bulk_clear_sync_flags (self, label_re=None):
        """See the documentation in folder.Folder"""

        if not label_re:
            label_re = 'asynk:[a-z][a-z]:id'

        logging.info('Fetching contact entries from Google for folder %s...',
                     self.get_name())

        feed = self._get_group_feed()
        if not feed.entry:
            return

        logging.info('Clearing sync state information...')

        ces  = feed.entry
        mods = []
        for i, ce in enumerate(ces):
            udp = []
            mod = False
            for ep in  ce.user_defined_field:
                if re.search(label_re, ep.key):
                    logging.info('  Iter %2d Tag %s match for item %s', 
                                 i, ep.key, ce.etag)
                    mod = True
                else:
                    ## Anything else, just put it back
                    udp.append(ep)

            ce.user_defined_field = udp
            if mod:
                mods.append(ce)

        logging.info('Uploading modifications to Google...')

        f     = self.get_db().new_feed()
        stats = BatchState(1, f, 'clear',)

        ret = True

        for cnt, ce in enumerate(mods):
            stats.add_con(ce.id.text, new=ce)
            f.add_update(entry=ce, batch_id_string=ce.id.text)
            stats.incr_cnt()

            if stats.get_cnt() % self.get_batch_size() == 0:
                # Feeds have to be less than 1MB. We can push this some
                # more. FIXME.
                logging.debug('Uploading clear batch # %02d to Google. ' +
                              'Count: %3d. Size: %6.2fK', stats.get_bnum(),
                              stats.get_cnt(), stats.get_size())
                rf = self.get_db().exec_batch(f)
                hr, ces = stats.process_batch_response(rf)
                ret = ret and hr

                f = self.get_db().new_feed()
                stats = BatchState(stats.get_bnum()+1, f, 'clear')

        # Upload any leftovers
        if stats.get_cnt() > 0:
            logging.debug('Uploading clear batch # %02d to Google. ' +
                          'Count: %3d. Size: %6.2fK', stats.get_bnum(),
                          stats.get_cnt(), stats.get_size())
            rf = self.get_db().exec_batch(f)
            hr, ces = stats.process_batch_response(rf)
            ret = ret and hr

        return ret
       
    def _refresh_contacts (self):
        feed = self._get_group_feed()
        for gce in feed.entry:
            gc = GCContact(self, gce=gce)
            self.add_contact(gc)

    def show (self, what='summary'):
        logging.info(str(self))
        logging.info('Summary of contained Items:')

        self._refresh_contacts()
        for itemid, con in self.get_contacts().iteritems():
            logging.info('  Name: %-25s Itemid: %s', con.get_name(), itemid)

    def __str__ (self):
        ret = 'Contacts'

        return ('%s.\tName: %s;\tGID: %s;\t' % (ret, self.get_name(),
                                                self.get_itemid()))

    ##
    ## Internal and helper routines
    ##

    def is_dirty (self):
        return self._get_prop('dirty')

    def is_clean (self):
        return not self.is_dirty()

    def set_clean (self):
        return self._set_prop('dirty', False)

    def set_dirty (self):
        return self._set_prop('dirty', True)

    def add_contact (self, gcc):
        self.contacts.update({gcc.get_itemid() : gcc})

    def reset_contacts (self):
        self.contacts = {}

    def get_contacts (self):
        return self.contacts    

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

    def add_con (self, olid_b64, new, orig=None):
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
        errors appropriately.

        Returns a tuple (success, cons) where success is a boolean to know if
        all the entries had successful operation, and an array of contact
        items from the batch operation"""
    
        op   = self.get_operation()
        cons = []
        success = True
    
        for entry in resp.entry:
            bid    = entry.batch_id.text if entry.batch_id else None
            if not entry.batch_status:
                # There is something seriously wrong with this request.
                logging.error('Unknown fatal error in response. Full resp: %s',
                              entry)
                success = False
                continue
    
            code   = int(entry.batch_status.code)
            reason = entry.batch_status.reason
    
            if code != SYNC_OK and code != SYNC_CREATED:
                # FIXME this code path needs to be tested properly
                err = sync_status_str(code)
                err_str = '' if err is None else ('Code: %s' % err)
                err_str = 'Reason: %s. %s' % (reason, err_str)
    
                success = False

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
                    logging.error('Could not complete sync for: %s: %s: %s',
                                  bid, err_str, entry.id)
                else:
                    ## We could just print a more detailed error for all
                    ## cases. Should do some time FIXME.
                    logging.error('Sync failed for bid %s: %s: %s',
                                   bid, err_str, entry.id)
            else:
                if op == 'query':
                    con = entry
                    # We could build and return array for all cases, but
                    # why waste memory...
                    cons.append(con)
                elif op in ['insert', 'update']:
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
    
        return success, cons
