##
## Created       : Tue Jul 19 15:04:46 IST 2011
## Last Modified : Tue Apr 03 18:57:07 IST 2012
##
## Copyright (C) 2011, 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
##
## This is the sync driver. At some point this might become the main driver
## replacing gout.py

# from   ol_wrapper    import Outlook
# from   ol_contact    import Contact
# from   gc_wrapper    import GC
# from   win32com.mapi import mapitags, mapiutil
# import atom, gdata.contacts.client

import getopt, logging, os, sys, traceback

if __name__ == "__main__":
    ## Being able to fix the sys.path thusly makes is easy to execute this
    ## script standalone from IDLE. Hack it is, but what the hell.
    DIR_PATH    = os.path.abspath(os.path.dirname(os.path.realpath('../Gout')))
    EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib')]
    sys.path = EXTRA_PATHS + sys.path

import state, utils
from   state         import Config
import demjson, base64

import atom, gdata, gdata.client
from   gdata.client import BadAuthentication
from   pimdb_gc     import GCPIMDB
import gdata.contacts.data, gdata.contacts.client

class Sync:
    BATCH_SIZE = 100

    def __init__ (self, config, f1, f2, dirn=None):
        self.atts = {}

        self.set_config(config)

        db1 = f1.get_db()
        db2 = f2.get_db()

        self.set_f1(f1)
        self.set_f2(f2)
        self.set_db1(db1)
        self.set_db2(db2)
        self.set_db1id(db1.get_dbid())
        self.set_db2id(db2.get_dbid())

        if not dirn:
            dirn = self.get_config().get_sync_dir(self.get_db1id(),
                                                  self.get_db2id())

        self.set_dir(dirn)

    ##
    ## First some internal helper routines
    ##

    def _get_att (self, key):
        return self.atts[key]

    def _set_att (self, key, val):
        self.atts[key] = val
        return val
              
    def get_config (self):
        return self._get_att('config')

    def set_config (self, config):
        return self._set_att('config', config)

    def get_f1 (self):
        return self._get_att('f1')

    def set_f1 (self, f1):
        return self._set_att('f1', f1)

    def get_f2 (self):
        return self._get_att('f2')

    def set_f2 (self, f2):
        return self._set_att('f2', f2)

    def get_db1 (self):
        return self._get_att('db1')

    def set_db1 (self, db1):
        return self._set_att('db1', db1)

    def get_db2 (self):
        return self._get_att('db2')

    def set_db2 (self, db2):
        return self._set_att('db2', db2)

    def get_db1id (self):
        return self._get_att('db1id')

    def set_db1id (self, db1id):
        return self._set_att('db1id', db1id)

    def get_db2id (self):
        return self._get_att('db2id')

    def set_db2id (self, db2id):
        return self._set_att('db2id', db2id)

    def get_dir (self):
        return self._get_att('dir')

    def set_dir (self, dir):
        return self._set_att('dir', dir)

    def reset_state (self):
        """Reset counters and other state information before starting."""
        pass

    def _prep_lists_2_way (self, f1, f2):
        """Identify the list of contacts that need to be copied from one
        place to the other and set the stage for the actual sync"""

        f1sl = SyncLists(f1)
        f2sl = SyncLists(f2)

        f1.prep_sync_lists(f2.get_dbid(), f1sl)
        f2.prep_sync_lists(f1.get_dbid(), f2sl)

        f1_mod = f1sl.get_mods()
        f2_mod = f2sl.get_mods()

        ## Identify potential conflicts in the modified lists and resolve them
        ## by deleting the conflict entries from one of the two lists

        # First create a list of matching entries. comd will be a dictionary
        # of common entries represented as a dictionary of 'f1_id : f2_id'
        # pairs: essentially an extract of the f1_mod
        coma = [id1 for id1,id2 in f1_mod.iteritems() if id2 in f2_mod.keys()]

        logging.info('Number of entries modified both places (conflicts): %d',
                     len(coma) if coma else 0)

        db1id = self.get_db1id()
        db2id = self.get_db2id()

        # The two db ids need to be specified in sorted order
        db1 = db1id if db1id < db2id else db2id
        db2 = db2id if db1id < db2id else db1id
        cr = self.get_config().get_conflict_resolve(db1, db2)

        if cr == db2id:
            f1_mod = f1sl.remove_keys(f1_mod, coma)
        elif cr == db1id:
            f2_mod = f2sl.remove_values(f2_mod, coma)
        else:
            logging.error('Unknown conflict resolution dir: %s', cr)

        logging.debug('conflict resolve direction : %s. db1id: %s, db2id: %s',
                      cr, db1id, db2id)
        logging.debug('After conflict resolution, size of f1_mod : %5d',
                      len(f1_mod))
        logging.debug('After conflict resolution, size of f2_mod : %5d',
                      len(f2_mod))

        return f1sl, f2sl

    def _prep_lists_1_way (self, f1, f2):
        logging.debug('_prep_lists_1_way(): ')
        f1sl = SyncLists(f1)
        f1.prep_sync_lists(f2.get_dbid(), f1sl)

        f1_mod = f1sl.get_mods()
        logging.debug('f: %s; size of mod: %d', f1.get_dbid(), len(f1_mod))

        return f1sl, None

    def _prep_lists (self):
        """Identify the list of contacts that need to be copied from one
        place to the other and set the stage for the actual sync"""

        dirn = self.get_dir()
        logging.debug('Direction: %s', dirn)
        if (dirn == 'SYNC2WAY'):
            return self._prep_lists_2_way(self.get_f1(), self.get_f2())
        elif (dirn == 'SYNC1WAY'):
            return self._prep_lists_1_way(self.get_f1(), self.get_f2())
        else:
            logging.error('_prep_lists(): Huh? Unknown sync dir in config: %s',
                          dirn)
            return None, None

    # def _fetch_gc_entries (self, gcids):
    #     """gcids is a list of google contact ids to retrieve contact
    #     entries for.

    #     Returns a list of ContactEntries"""

    #     gid    = self.config.get_gid()
    #     f      = self.gc.new_feed()
    #     stats = Sync.BatchState(1, f, 'query')

    #     ret = []

    #     for gcid in gcids:
    #         ce = gdata.contacts.data.ContactEntry()
    #         ce.id = atom.data.Id(text=gcid)
    #         stats.add_con(gcid, ce)

    #         f.add_query(entry=ce, batch_id_string=gcid)
    #         stats.incr_cnt()

    #         if stats.get_cnt() % self.BATCH_SIZE == 0:
    #             # Feeds have to be less than 1MB. We can push this some
    #             # more
    #             logging.debug('Qry Batch # %02d. Count: %3d. Size: %6.2fK',
    #                           stats.get_bnum(), stats.get_cnt(),
    #                           stats.get_size())

    #             rf  = self.gc.exec_batch(f)
    #             ces = self.process_batch_response(rf, stats)
    #             [ret.append(x) for x in ces]

    #             f = self.gc.new_feed()
    #             s = Sync.BatchState(stats.get_bnum()+1, f, 'query')
    #             stats = s

    #     # Process any leftovers
    #     if stats.get_cnt() > 0:
    #         logging.debug('Qry Batch # %02d. Count: %3d. Size: %5.2fK',
    #                       stats.get_bnum(), stats.get_cnt(),
    #                       stats.get_size())
            
    #         rf  = self.gc.exec_batch(f)
    #         ces = self.process_batch_response(rf, stats)
    #         [ret.append(x) for x in ces]

    #     return ret

    # def _get_new_gc_to_ol (self):
    #     logging.info('=====================================================')
    #     logging.info('   Fetching new entries from Google Contacts')
    #     logging.info('=====================================================')
    #     logging.info('Querying status from Google...')

    #     ces = self._fetch_gc_entries(self.gc.get_con_new())
    #     if ces and len(ces)>0:
    #         resp = '%d new entries created on Google will be copied.' % len(ces)
    #     else:
    #         resp = 'No new contacts found in Google Contacts. Nothing to copy.'

    #     logging.info(resp)

    #     self._write_ces_to_ol(ces)

    # def _get_mod_gc_to_ol (self):
    #     """Fetch the entries that we know have been modified on Google side
    #     and that we want to store in Outlook."""

    #     logging.info('=====================================================')
    #     logging.info('   Fetching modified entries from Google Contacts')
    #     logging.info('=====================================================')
    #     logging.info('Querying status from Google...')

    #     ces = self._fetch_gc_entries(self.gc.get_con_mod().keys())

    #     if ces and len(ces)>0:
    #         resp = '%d modified contacts from Google will be copied.' % len(ces)
    #     else:
    #         resp = 'No contacts modified in Google Contacts. Nothing to copy.'

    #     logging.info(resp)

    #     # Synching entries modified on Google is nothing but deleting local
    #     # copies in Outlook and creating fresh entries. This is hack, and in
    #     # future we might decide to implement a 'inplace' updatiion. TODO.
    #     self._write_ces_to_ol(ces)

    #     eids = [base64.b64decode(x) for x in self.gc.get_con_mod().values()]
    #     self.olcf.del_entries(eids)

    # def _write_ces_to_ol (self, ces, writeback_olid=True):
    #     """ces is a list of ContactEntry objects which need to be saved to
    #     outlook. If the entires do not exist in Outlook we will need to save
    #     hte Outlook EntryIDs to Google on successful save to Outlook. This
    #     step can be skipped if we are only writing modifications and an entry
    #     already exists in Outlook. The writeback behaviour is controlled by
    #     the value of the writeback_olid parameter."""

    #     f = self.gc.new_feed()
    #     stats = Sync.BatchState(1, f, 'Writeback olid')

    #     for ce in ces:
    #         c  = Contact(fields=self.fields, config=self.config,
    #                      ol=self.ol, entryid=None, props=None,
    #                      gcapi=self.gc, gcentry=ce, data_from_ol=False)

    #         # Save changes in Outlook and write back the olid to the Google
    #         # Entry

    #         eid = c.push_to_outlook()
    #         bid = base64.b64encode(eid)
    #         stats.add_con(bid, c)

    #         ce = self.gc.add_olid_to_ce(ce, eid)

    #         if (writeback_olid):
    #             f.add_update(entry=ce, batch_id_string=bid)
    #             stats.incr_cnt()

    #             if stats.get_cnt() % self.BATCH_SIZE == 0:
    #                 logging.info('Uploading Oulook EntryIDs to Google...')
    #                 logging.debug('Batch #%02d. Count: %3d. Size: %6.2fK',
    #                               stats.get_bnum(), stats.get_cnt(),
    #                               stats.get_size())
    
    #                 rf = self.gc.exec_batch(f)
    #                 self.process_batch_response(rf, stats)
     
    #                 f = self.gc.new_feed()
    #                 s = Sync.BatchState(stats.get_bnum()+1, f, 'Writeback olid')
    #                 stats = s

    #     # Upload any leftovers
    #     if writeback_olid and stats.get_cnt() > 0:
    #         logging.info('Uploading Oulook EntryIDs to Google...')
    #         logging.debug('Batch # %02d. Count: %3d. Size: %5.2fK',
    #                       stats.get_bnum(), stats.get_cnt(),
    #                       stats.get_size())
    #         rf = self.gc.exec_batch(f)
    #         self.process_batch_response(rf, stats)

    def _del_ol (self):
        pass

    def _del_gc (self):
        pass

    def _reset_sync (self):
        """Delete all sync related information on Gmail and in Outlook,
        delete the old group and all its contacts, and create a fresh
        group with a new group ID - in sum, make a fresh beginning."""

        self.gc.clear_sync_state()
        self.olcf.bulk_clear_gcid_flag()
        self.gc.clear_group(gid=self.config.get_gid(), gentry=None)

        gc_gid = self.gc.create_group(self.config.get_gn())
        self.config.set_gid(gc_gid)

    def dry_run (self):
        try:
            self._prep_lists()
            ret = self.olcf.all_entries()
            print 'Folder Name: ', ret['folder']
            print 'Store  Name: ', ret['store']
            print 'Entry Count: ', ret['entrycnt']
        except Exception, e:
            logging.critical('Internal Error: %s', str(e))
            logging.critical('Full Traceback follows.\n%s',
                          traceback.format_exc())

    def run (self):
        self._prep_lists()

        if (self.dir == state.SYNC_2_WAY or
            self.dir == state.SYNC_1_WAY_O2G):
            self._send_new_ol_to_gc()
            self._send_mod_ol_to_gc()
            self._del_gc()

        if (self.dir == state.SYNC_2_WAY or
            self.dir == state.SYNC_1_WAY_G2O):
            self._get_new_gc_to_ol()
            self._get_mod_gc_to_ol()
            self._del_ol()

class SyncLists:
    """Wrapper around lists of items that need to be synched from one place to
    another. Just for convenience."""

    def __init__ (self, src_fold):
        """fold is the source for the entries."""
        self.fold  = src_fold
        self.db1id = self.fold.get_dbid()

        # Has of ID to Etag where appliable (like in Google Contacts. or just
        # a ID : None mapping to mark presence.
        self.all  = {}
        self.news = []
        self.mods = {}                    # Hash of f1 id -> f2 id
        self.dels = {}

    def remove_keys (self, d, k):
        """Remove all the keys specified in the array k from the passed
        dictionary and return the new dictionary. This routine is typically
        used to manipulate one of the self.dictoinaries."""

        d = dict([(x,y) for x,y in d.iteritems() if not x in k])
        return d

    def remove_values (self, d, v):
        """Remove all the values specified in the array k from the passed
        dictionary and return the new dictionary. This routine is typically
        used to manipulate one of the self.dictoinaries."""

        d = dict([(x,y) for x,y in d.iteritems() if not y in v])
        return d

    def add_new (self, fid):
        self.news.append(fid)

    def add_mod (self, f1id, f2id):
        self.mods.update({f1id : f2id})

    def add_del (self, f1id, f2id):
        self.dels.update({f1id : f2id})

    def entry_exists (self, f1id):
        try:
            val = self.all[f1id]
            return True
        except KeyError, e:
            return False

    def add_entry (self, f1id, f2id):
        self.add_etag(f1id, f2id)

    def get_entries (self):
        return self.all.keys()

    ## Just an alias for add_entry; used to clarify the nature of the value
    ## being added.
    def add_etag (self, f1id, f2id):
        self.all.update({f1id : f2id})

    def get_etag (self, f1id):
        return self.all[f1id]

    def get_news (self):
        return self.news

    def get_mods (self):
        return self.mods

    def get_dels (self):
        return self.mods

    def send_news_to_folder (self, df):
        """df is the destination folder."""

        logging.info('=====================================================')
        logging.info('   Sending New %s entries to %s',
                     self.db1id, df.get_dbid())
        logging.info('=====================================================')
        if len(self.get_news()):
            logging.info('%d new entries to be synched.', len(self.get_news()))
        else:
            logging.info('No new entries that need to be synched')
            return

        items = self.fold.find_items(self.get_news())
        df.batch_create(self, self.db1id, items)
        self.fold.writeback_sync_tags(items)

    ## FIXME: There appears to be a lot of code repitition between the above
    ## routine and this one. Eplore how to eliminate this stuff...
    def send_mods_to_folder (self, df):
        """df is the destination folder."""
        logging.info('=====================================================')
        logging.info('   Sending Modified %s entries to %s',
                     self.db1id, df.get_dbid())
        logging.info('=====================================================')
        if len(self.get_mods()):
            logging.info('%d modified entries to be synched.',
                         len(self.get_mods()))
        else:
            logging.info('No modified entries that need to be synched')
            return

        items = self.fold.find_items(self.get_mods())
        df.batch_update(self, self.db1id, items)

    def send_dels_to_folder (self, df):
        """df is the destination folder."""
        logging.debug('send_dels_to_folder: unimplemented')

    def sync_to_folder (self, df):
        self.send_news_to_folder(df)
        self.send_mods_to_folder(df)
        self.send_dels_to_folder(df)

def main ():
    tests = TestSync()

    # tests.test_sync_status()
    tests.test_sync()

    # tests.test_clear_ol_sync_flags()

    # tests.del_gcid('AAAAADWE5+lnNclLmn8GpZUD04fEQGMA')
    # tests.read_gcid('AAAAADWE5+lnNclLmn8GpZUD04ekQGMA')

class TestSync:
    def __init__ (self):
        self.config = Config('../app_state.json')
        self.pimgc = self._login_gc()
        self.pimol = self._login_ol()

    def _login_gc (self):
        # The following is the 'Gout' group on karra.etc@gmail.com
        self.gid = 'http://www.google.com/m8/feeds/groups/karra.etc%40gmail.com/base/41baff770f898d85'

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
            pw = raw_input('Password: ')
            if not pw:
                print 'Password cannot be blank'

        try:
            return GCPIMDB(self.config, user, pw)
        except BadAuthentication:
            print 'Invalid credentials. WTF.'
            raise

    def _login_ol (self):
        from pimdb_ol import OLPIMDB

        return OLPIMDB(self.config)

    def del_gcid (self, itemid):
        ## This should really go into contact_ol.py
        from win32com.mapi import mapi, mapitags
        import winerror
        from contact_ol import OLContact

        olcf     = self.pimol.get_def_folder()
        eid      = base64.b64decode(itemid)
        
        prop_tag = olcf.get_proptags().valu('ASYNK_PR_GCID')
        store    = olcf.get_msgstore()
        item     = store.get_obj().OpenEntry(eid, None, mapi.MAPI_BEST_ACCESS)

        hr, ps = item.DeleteProps([prop_tag])
        item.SaveChanges(mapi.KEEP_OPEN_READWRITE)

        if winerror.FAILED(hr):
            logging.info('Failed to clear GCID for itemid: %s (%s)',
                         itemid, winerror.HRESULT_CODE(hr))
        else:
            logging.info('Successfully Cleared GCID for itemid: %s', itemid)

    def read_gcid (self, itemid):
        ## This should really go into contact_ol.py
        from win32com.mapi import mapi, mapitags
        from contact_ol import OLContact

        olcf     = self.pimol.get_def_folder()
        eid      = base64.b64decode(itemid)

        prop_tag = olcf.get_proptags().valu('ASYNK_PR_GCID')
        store    = olcf.get_msgstore()
        item     = store.get_obj().OpenEntry(eid, None, mapi.MAPI_BEST_ACCESS)

        hr, props = item.GetProps([prop_tag], mapi.MAPI_UNICODE)
        (tag, val) = props[0]
        if mapitags.PROP_TYPE(tag) == mapitags.PT_ERROR:
            print 'Prop_Tag (0x%16x) not found. Tag: 0x%16x' % (prop_tag,
                                                                (tag % (2**64)))
        else:
            print 'Google ID found for contact. ID: ', val

    def test_sync_status (self):
        olcf = self.pimol.get_def_folder()
        gccf = self.find_group(self.gid)

        self.sync = Sync(self.config, gccf, olcf)
        self.sync._prep_lists()

    def test_sync (self):
        logging.debug('test_sync()... Starting Sync to Outlook')
        olcf = self.pimol.get_def_folder()
        gccf = self.find_group(self.gid)

        self.sync = Sync(self.config, olcf, gccf)
        sl1, sl2 = self.sync._prep_lists()
        sl1.sync_to_folder(gccf)
        sl2.sync_to_folder(olcf)
        logging.debug('test_sync()... Finished Sync')

    def test_clear_ol_sync_flags (self):
        olcf = self.pimol.get_def_folder()
        olcf.bulk_clear_sync_flags(['bb', 'gc'])

    def find_group (self, gid):
        gc, ftype = self.pimgc.find_folder(gid)
        if gc:
            print 'Found the sucker. Name is: ', gc.get_name()
            return gc
        else:
            print 'D''oh. Folder not found.'
            return

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    try:
        main()
    except Exception, e:
        print 'Caught Exception... Hm. Need to cleanup.'
        print 'Full Exception as here:', traceback.format_exc()

## FIXME: Needs more thorough unit testing.
