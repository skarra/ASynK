##
## Created : Tue Jul 19 15:04:46 IST 2011
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
## ####
##

import logging, os

from   state         import Config
import demjson

import atom, gdata
from   gdata.client import BadAuthentication
from   pimdb_gc     import GCPIMDB
import gdata.contacts.data, gdata.contacts.client

class Sync:
    BATCH_SIZE = 100

    def __init__ (self, config, profile, pimdbs, dirn=None, dr=False):
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

        db1 = self.get_db(0)
        db2 = self.get_db(1)

        logging.debug('db    : %s', db1)

        if fid1 == 'default':
            fid1 = db1.get_def_folder().get_itemid()
            logging.debug('Updated fid1  : %s', fid1)

        if fid2 == 'default':
            fid2 = db2.get_def_folder().get_itemid()
            logging.debug('Updated fid2  : %s', fid2)

        f1 = db1.find_folder(fid1)[0]
        if f1:
            self.set_f1(f1)
        else:
            ## We may have to create a folder we are processing a BBDB database.
            logging.error('Could not find folder with ID fid1: %s', fid1)
            if self.get_db1id() == 'bb':
                logging.error('Creating BBBD folder %s in store', fid1)
                f1 = db1.new_folder(fid1)
                self.set_f1(f1)
            else:
                raise Exception()

        f2 = db2.find_folder(fid2)[0]
        if f2:
            self.set_f2(f2)
        else:
            ## We may have to create a folder we are processing a BBDB database.
            logging.error('Could not find folder with ID fid2: %s', fid2)
            if self.get_db2id() == 'bb':
                logging.error('Creating BBBD folder %s in store', fid2)
                f2 = db2.new_folder(fid2)
                self.set_f2(f2)
            else:
                raise Exception()

        db1.prep_for_sync(self.get_db2id(), profile, dr)
        db2.prep_for_sync(self.get_db1id(), profile, dr)

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

        f1sl.log_print_stats()
        f2sl.log_print_stats()

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

        ## FIXME: The following commented out code appears very fishy. I am
        ## not able to recall why these two have to be used in sorted order. I
        ## am pretty sure there was some sense behind it, but as of now db1
        ## and db2 are not really being used; so the code works even without
        ## this "sorted" behaviour... Hm, this really should go, but I am
        ## being conservative here and leving the stuff commented out so we
        ## can come back to it later if required.

        # # The two db ids need to be specified in sorted order
        # db1 = db1id if db1id < db2id else db2id
        # db2 = db2id if db1id < db2id else db1id

        cr = self.get_config().get_conflict_resolve(pname)

        if cr == db2id or cr == "2":
            f1_mod = f1sl.remove_keys_from_mod(coma)
        elif cr == db1id or cr == "1":
            f2_mod = f2sl.remove_values_from_mod(coma)
        else:
            logging.error('Unknown conflict resolution dir: %s', cr)

        logging.info('conflict resolve direction : %s. db1id: %s, db2id: %s',
                      cr, db1id, db2id)
        logging.info('After conflict resolution, size of %s mod : %5d',
                     db1id, len(f1_mod))
        logging.info('After conflict resolution, size of %s mod : %5d',
                     db2id, len(f2_mod))

        ## Now we need to process the deletes as well

        f1_del = f1sl.get_dels()
        f2_del = f2sl.get_dels()

        coma = [y for x,y in f1_del.iteritems() if y in f2_mod.keys()]
        f2_mod = f2sl.remove_keys_from_mod(coma)

        coma = [y for x,y in f2_del.iteritems() if y in f1_mod.keys()]
        f1_mod = f1sl.remove_keys_from_mod(coma)

        logging.debug('After removing dels from mod, size of %s mod : %5d',
                      db1id, len(f1_mod))
        logging.debug('After removing dels from mod, size of %s mod : %5d',
                      db2id, len(f2_mod))

        # Finally remove entries that have been deleted from both places. Why
        # bother with these suckers?
        coma = dict([(x,y) for x,y in f1_del.iteritems() if y in f2_del.keys()])
        f2_del = f2sl.remove_keys_from_del(coma.values())
        for x in coma.keys():
            del f1_del[x]

        coma = dict([(x,y) for x,y in f2_del.iteritems() if y in f1_del.keys()])
        f1_del = f1sl.remove_keys_from_del(coma.values())
        for x in coma.keys():
            del f2_del[x]

        logging.info('After conflict resolution, size of %s del : %5d',
                     db1id, len(f1_del))
        logging.info('After conflict resolution, size of %s del : %5d',
                     db2id, len(f2_del))

        return f1sl, f2sl

    def _prep_lists_1_way (self, f1, f2):
        logging.debug('_prep_lists_1_way(): ')
        f1sl = SyncLists(f1, self.get_pname())
        f1.prep_sync_lists(f2.get_dbid(), f1sl)
        f1sl.log_print_stats()

        f1_mod = f1sl.get_mods()
        logging.debug('f: %s; size of mod: %d', f1.get_dbid(), len(f1_mod))

        return f1sl, None

    def prep_lists (self, dirn):
        """Identify the list of contacts that need to be copied from one
        place to the other and set the stage for the actual sync"""

        logging.info('Last synk for profile %s was at: %s', self.get_pname(),
                     self.get_config().get_last_sync_stop(self.get_pname()))

        if (dirn == 'SYNC2WAY'):
            return self._prep_lists_2_way(self.get_f1(), self.get_f2())
        elif (dirn == 'SYNC1WAY'):
            return self._prep_lists_1_way(self.get_f1(), self.get_f2())
        else:
            logging.error('_prep_lists(): Huh? Unknown sync dir in config: %s',
                          dirn)
            return None, None

    def sync (self, dirn=None):
        if not dirn:
            dirn = self.get_dir()

        sl1, sl2 = self.prep_lists(dirn)

        ret2 = True
        ret1 = sl1.sync_to_folder(self.get_f2())
        if dirn == 'SYNC2WAY':
            ret2 = sl2.sync_to_folder(self.get_f1())

        return ret1 and ret2

    def save_item_lists (self):
        """Write the existing item list to file, so we can identify deletes
        between now and a subsequent run."""

        # This is a potentially tricky operation, because if this is
        # interrupted and only a partial list gets written to disk, the system
        # could think there are way too many deletes... Hm. We have to build
        # in some defensive manouvers shortly.

        conf = self.get_config()
        prof = self.get_pname()

        items1 = self.get_f1().get_itemids(prof, self.get_db2id())

        conf.set_itemids(prof, items1)

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
        self.unmods = []

        self.pname = pname

    def get_pname (self):
        return self.pname

    def remove_keys_from_mod (self, k):
        """Remove all the keys specified in the array k from the passed
        dictionary and return the new dictionary. This routine is typically
        used to manipulate one of the self.dictoinaries."""

        d = self.get_mods()
        d = dict([(x,y) for x,y in d.iteritems() if not x in k])

        return self.set_mods(d)

    def remove_values_from_mod (self, v):
        """Remove all the values specified in the array k from the passed
        dictionary and return the new dictionary. This routine is typically
        used to manipulate one of the self.dictoinaries."""

        d = self.get_mods()
        d = dict([(x,y) for x,y in d.iteritems() if not y in v])

        return self.set_mods(d)

    def remove_keys_from_del (self, k):
        """Remove all the keys specified in the array k from the passed
        dictionary and return the new dictionary. This routine is typically
        used to manipulate one of the self.dictoinaries."""

        d = self.get_dels()
        d = dict([(x,y) for x,y in d.iteritems() if not x in k])

        return self.set_dels(d)

    def remove_values_from_del (self, v):
        """Remove all the values specified in the array k from the passed
        dictionary and return the new dictionary. This routine is typically
        used to manipulate one of the self.dictoinaries."""

        d = self.get_dels()
        d = dict([(x,y) for x,y in d.iteritems() if not y in v])

        return self.set_dels(d)

    def add_new (self, fid):
        self.news.append(fid)

    def add_mod (self, f1id, f2id):
        self.mods.update({f1id : f2id})

    def add_unmod (self, fid):
        self.unmods.append(fid)

    def add_del (self, f1id, f2id):
        self.dels.update({f1id : f2id})

    def entry_exists (self, f1id):
        return f1id in self.all

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

    def get_unmods (self):
        return self.unmods

    def set_mods (self, val):
        self.mods = val
        return val

    def get_dels (self):
        return self.dels

    def set_dels (self, val):
        self.dels = val
        return val

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
            return True

        items = self.fold.find_items(self.get_news())
        res = df.batch_create(self, self.db1id, items)
        res = res and self.fold.writeback_sync_tags(self.get_pname(), items)

        return res

    def log_print_stats (self):
        total = (len(self.get_news()) + len(self.get_mods()) +
                 len(self.get_unmods()))

        logging.info('==== %s =====', self.db1id)
        logging.info('   New              : %5d', len(self.get_news()))
        logging.info('   Modified         : %5d', len(self.get_mods()))
        logging.info('   Unchanged        : %5d', len(self.get_unmods()))
        logging.info('                      =====')
        logging.info('   Total Entries    : %5d', total)
        logging.info('   Deleted          : %5d', len(self.get_dels()))

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
            return True

        items = self.fold.find_items(self.get_mods())
        res = df.batch_update(self, self.db1id, items)

        return res

    def send_dels_to_folder (self, df):
        """df is the destination folder."""
        logging.info('=====================================================')
        logging.info('   Synching Deleted %s entries to %s',
                     self.db1id, df.get_dbid())
        logging.info('=====================================================')

        remids = self.get_dels().values()
        if len(remids) > 0:
            df.del_itemids(remids)
        else:
            logging.info('No deleted entries that need to be synched.')

        return True

    def sync_to_folder (self, df):
        res1 = self.send_news_to_folder(df)
        res2 = self.send_mods_to_folder(df)
        res3 = self.send_dels_to_folder(df)

        return res1 and res2 and res3
