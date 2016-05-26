##
## Created : Wed May 18 13:16:17 IST 2011
##
## Copyright (C) 2011, 2012, 2013 Sriram Karra <karra.etc@gmail.com>
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

import copy, logging, re
from   abc            import ABCMeta, abstractmethod
from   folder         import Folder
from   contact_gc     import GCContact
import xml.etree.ElementTree as ET

import utils
import atom, gdata.contacts.client

class AddHeader:
    def __init__ (self):
        pass

    def modify_request (self, http_request):
        http_request.headers["If-Match"] = "*"

eh = None # AddHeader()

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
    """A class that wraps a Google Contacts folder of label."""

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
        pdb1id = conf.get_profile_db1(pname)
        oldi  = conf.get_itemids(pname)
        newi  = self.get_itemids(pname, destid)

        kss = newi.keys()
        for x, y in oldi.iteritems():
            if not x in kss and not y in kss:
                logging.debug('Del      Google Contact: %s:%s', x, y)
                if pdb1id == self.get_dbid():
                    sl.add_del(x, y)
                else:
                    sl.add_del(y,x)

        logging.info('Querying Google for status of Contact Entries...')
        stag = conf.make_sync_label(pname, destid)

        ## FIXME: The following commented out code appears very fishy. I am
        ## not able to recall why these two have to be used in sorted order. I
        ## am pretty sure there was some sense behind it, but as of now db1
        ## and db2 are not really being used; so the code works even without
        ## this "sorted" behaviour... Hm, this really should go, but I am
        ## being conservative here and leving the stuff commented out so we
        ## can come back to it later if required.

        # ## Sort the DBIds so dest1 has the 'lower' ID
        # db1 = self.get_db().get_dbid()
        # if db1 > destid:
        #     db2 = db1
        #     db1 = destid
        # else:
        #     db2 = destid

        if not updated_min:
            updated_min = conf.get_last_sync_stop(pname)

        # FIXME: We are fetching the group feed a second time. Ideally we
        # shoul dbe able to everything we want with the feed already fetched
        # above. This has a performance implication for groups with a large
        # number of items. Will fix this once functionality is validated.
        feed = self._get_group_feed(updated_min=updated_min, showdeleted='false')

        logging.info('Response recieved from Google. Processing...')

        if not feed.entry:
            logging.info('No entries in feed.')

            for x in kss:
                sl.add_unmod(x)

            return

        skip     = 0
        etag_cnt = 0

        for i, entry in enumerate(feed.entry):
            gcid = utils.get_link_rel(entry.link, 'edit')
            gcid = GCContact.normalize_gcid(gcid)
            olid = get_udp_by_key(entry.user_defined_field, stag)
            etag = entry.etag
            epd  = entry.deleted
            name = None
            if entry.name:
                if entry.name.full_name:
                    name = entry.name.full_name.text
                elif entry.name.family_name:
                    name = entry.name.family_name.text
                elif entry.name.given_name:
                    name = entry.name.given_name.text

            if epd:
                if olid:
                    pass
                    # We will trust our own delete logic...
                    # sl.add_del(gcid)
                else:
                    # Deleted before it got synched. Get on with life
                    skip += 1
                    continue
            else:
                if olid:
                    logging.debug('Modified Google Contact: %20s %s', 
                                  name, gcid)
                    sl.add_mod(gcid, olid)
                else:
                    logging.debug('New      Google Contact: %20s %s', 
                                  name, gcid)
                    sl.add_new(gcid)

            if etag:
                sl.add_etag(gcid, etag)
                etag_cnt += 1
            else:
                sl.add_entry(gcid)

        for x in kss:
            if not x in sl.get_news() and not x in sl.get_mods():
                sl.add_unmod(x)

        logging.debug('Total Contacts   : %5d', len(newi))
        logging.debug('num with etags   : %5d', etag_cnt)
        logging.debug('num del bef sync : %5d', skip)

    def get_itemids (self, pname, destid):
        self._refresh_contacts()
        ret = {}
        stag = self.get_config().make_sync_label(pname, destid)
        for locid, con in self.get_contacts().iteritems():
            if stag in con.get_sync_tags():
                t, remid = con.get_sync_tags(stag)[0]
                ret.update({locid : remid})

        return ret

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
        pname   = src_sl.get_pname()

        src_sync_tag = c.make_sync_label(src_sl.get_pname(), src_dbid)
        dst_sync_tag = c.make_sync_label(src_sl.get_pname(), my_dbid)

        f     = self.get_db().new_feed()
        stats = BatchState(1, f, 'insert', sync_tag=dst_sync_tag)

        success = True
        for item in items:
            con_itemid = item.get_itemid_from_synctags(pname, 'gc')
            gc  = GCContact(self, con=item, con_itemid=con_itemid)
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
            gcid = GCContact.normalize_gcid(gcid)
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
            con_itemid = item.get_itemid_from_synctags(pname, 'gc')
            gc  = GCContact(self, con=item, con_itemid=con_itemid)
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
                rf = self.get_db().exec_batch(f, extra_headers=eh)
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
            rf = self.get_db().exec_batch(f, extra_headers=eh)
            succ, cons = stats.process_batch_response(rf)
            success = success and succ

        return success

    def writeback_sync_tags (self, pname, items):
        conf  = self.get_config()
        remid = conf.get_other_dbid(pname, self.get_dbid())
        stag  = conf.make_sync_label(pname, remid)

        f     = self.get_db().new_feed()
        stats = BatchState(1, f, 'Writeback olid', sync_tag=stag)

        success = True
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

                rf = self.get_db().exec_batch(f, extra_headers=eh)
                succ, cons = stats.process_batch_response(rf)
                success = success and succ

                f = self.get_db().new_feed()
                stats = BatchState(stats.get_bnum()+1, f, 'Writeback olid',
                                   sync_tag=stag)
           
        # Upload any leftovers
        if stats.get_cnt() > 0:
            logging.info('Uploading Remote ItemIDs to Google...')
            logging.debug('Batch # %02d. Count: %3d. Size: %5.2fK',
                          stats.get_bnum(), stats.get_cnt(),
                          stats.get_size())

            rf = self.get_db().exec_batch(f, extra_headers=eh)
            succ, cons = stats.process_batch_response(rf)
            success = success and succ

        return success

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
        cnt  = 0
        for i, ce in enumerate(ces):
            udp = []
            mod = False
            for ep in  ce.user_defined_field:
                if re.search(label_re, ep.key):
                    logging.debug('  Iter %2d Tag %s match for item %s', 
                                  i, ep.key, ce.etag)
                    cnt += 1
                    mod = True
                else:
                    ## Anything else, just put it back
                    udp.append(ep)

            ce.user_defined_field = udp
            if mod:
                mods.append(ce)

        logging.info('Found %d contacts with matching sync tags (%s). ',
                     cnt, label_re)
        if cnt > 0:
            logging.info('Sending modification request to Google...')

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

        if cnt > 0:
            logging.info('Sending modification request to Google...Done')

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

    def del_itemids (self, itemids):
        """Remove the specified from the contact from this folder, and return
        True. If it does not exist in the folder, returns False."""

        success, cons = self._fetch_gc_entries(itemids)
        for con in cons:
            logging.info('Deleting ID: %s; Name: %s...', con.id.text,
                         con.name.full_name.text if con.name else '')
            self.get_gdc().Delete(con)
            try:
               del self.contacts[con.id.text]
            except KeyError, e:
               pass 

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

    def handle_interrupted_feed (self, resp_xml):
        resp = ET.fromstring(resp_xml)
        ffc = utils.find_first_child

        resp_title = ffc(resp, utils.QName_GNS0('title'), ret='node').text
        resp_intr  = ffc(resp, utils.QName_GNS3('interrupted'), ret='node')

        parsed = int(resp_intr.attrib['parsed'])
        reason = resp_intr.attrib['reason']

        entry = self.f.entry[parsed]
        logging.error('The server encountered a %s while processing ' +
                      'the feed. The reason given is: %s', resp_title,
                      resp_intr)
        logging.error('The problematic entry is likely this one: %s',
                      utils.pretty_xml(str(entry)))

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
                self.handle_interrupted_feed(str(resp))
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
                        name = self.get_con(bid).get_disp_name()
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
                    gcid = GCContact.normalize_gcid(gcid)
                    orig.update_sync_tags(self.sync_tag, gcid)
                    cons.append(orig)

                    t = None
                    if op == 'insert':
                        t = 'created'
                    elif op == 'update':
                        t = 'updated'
    
                    if t:
                        logging.info('Successfully %s gmail entry for %30s (%s)',
                                     t, con.get_disp_name(), orig.get_itemid())
    
        return success, cons
