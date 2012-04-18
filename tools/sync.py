##
## Created       : Tue Jul 19 15:04:46 IST 2011
## Last Modified : Wed Apr 18 14:08:35 IST 2012
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

    def __init__ (self, config, profile, pimdbs, dirn=None):
        """dirn is one of the syn directions, and can be used to override the
        default sync direction stored in the profile. It is then used as the
        default sync direction for future runs.

        pimdbs is a dictionary of PIMDB intances indexed by their dbids. We
        should really be loggingin here if pimdbs is None... Hm"""

        self.atts = {}

        self.set_config(config)
        self.set_pname(profile)
        self.set_pimdbs(pimdbs)

        fid1 = config.get_fid1(profile)
        fid2 = config.get_fid2(profile)

        logging.debug('pimdbs : %s', pimdbs)
        logging.debug('pname : %s', profile)
        logging.debug('fid1  : %s', fid1)
        logging.debug('fid2  : %s', fid2)
        logging.debug('db1id : %s', self.get_db1id())

        db1 = self.get_db(self.get_db1id())
        db2 = self.get_db(self.get_db2id())

        logging.debug('db    : %s', db1)

        self.set_f1(db1.find_folder(fid1)[0])
        self.set_f2(db2.find_folder(fid2)[0])

        db1.prep_for_sync(self.get_db2id())
        db2.prep_for_sync(self.get_db1id())

        if dirn:
            self.set_dir(dirn)
        else:
            dirn = self.get_dir()

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

    def get_pname (self):
        return self._get_att('pname')

    def set_pname (self, pname):
        return self._set_att('pname', pname)

    def get_db (self, dbid):
        return self._get_att('pimdbs')[dbid]

    def set_pimdbs (self, val):
        return self._set_att('pimdbs', val)

    def get_f1 (self):
        return self._get_att('f1')

    def set_f1 (self, f):
        return self._set_att('f1', f)

    def get_f2 (self):
        return self._get_att('f2')

    def set_f2 (self, f):
        return self._set_att('f2', f)

    def get_db1 (self):
        return self._get_att('db1')

    def get_db2 (self):
        dbid = self.get_db2id()
        return self.get_db(dbid)

    def get_db1id (self):
        return self.get_config().get_profile_db1(self.get_pname())

    def get_db2id (self):
        return self.get_config().get_profile_db2(self.get_pname())

    def get_dir (self):
        return self.get_config().get_sync_dir(self.get_pname())

    def set_dir (self, dir):
        return self.get_config().set_sync_dir(self.get_pname(), dir)

    def reset_state (self):
        """Reset counters and other state information before starting."""
        pass

    def _prep_lists_2_way (self, f1, f2):
        """Identify the list of contacts that need to be copied from one
        place to the other and set the stage for the actual sync"""

        pname = self.get_pname()
        f1sl  = SyncLists(f1, pname)
        f2sl  = SyncLists(f2, pname)

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
        cr = self.get_config().get_conflict_resolve(pname)

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
        f1sl = SyncLists(f1, self.get_pname())
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

    def __init__ (self, src_fold, pname):
        """fold is the source for the entries."""
        self.fold  = src_fold
        self.db1id = self.fold.get_dbid()

        # Has of ID to Etag where appliable (like in Google Contacts. or just
        # a ID : None mapping to mark presence.
        self.all  = {}
        self.news = []
        self.mods = {}                    # Hash of f1 id -> f2 id
        self.dels = {}

        self.pname = pname

    def get_pname (self):
        return self.pname

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
        return self.dels

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
