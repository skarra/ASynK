##
## Created       : Tue Jul 19 13:54:53 IST 2011
## Last Modified : Tue Apr 10 17:05:22 IST 2012
##
## Copyright (C) 2011, 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
## 

import iso8601, demjson
import logging, os, time, traceback

import utils

sync_dirs = ['SYNC1WAY', 'SYNC2WAY']

class GoutConfigError(Exception):
    pass

class Config:
    def __init__ (self, fn, sync_through=True):
        """If sync_through is True, any change to the configuration is
        immediately written back to the original disk file, otherwise
        the user has to explicitly save to disk."""

        fi = None
        self.fn = os.path.abspath(fn)
        self.sync_through = False

        try:
            fi = open(fn, "r")
        except IOError, e:
            logging.critical('Error! Could not Open file (%s): %s', fn, e)
            return

        st = fi.read()
        self.inp = demjson.decode(st)
        fi.close()

        self.state = self.inp

        self.sync_through = sync_through

    ##
    ## Helper routines
    ##

    ## Not dependent on sync state between a pair of PIMDs

    def _get_prop (self, key):
        return self.state[key]

    def _set_prop (self, key, val, sync=True):
        self.state[key] = val
        if self.sync_through and sync:
            self.save()

    def _append_to_prop (self, key, val, sync=True):
        """In the particular property value is an array, we would like to
        append individual elements to the property value. this method does
        exactly that."""

        if not self.state[key]:
            self.state[key] = [val]
        else:
            self.state[key].append(val)

        if self.sync_through and sync:
            self.save()

    def _update_prop (self, prop, which, val, sync=True):
        """If a particular property value is a dictionary, we would like to
        update the dictinary with a new mapping or alter an existing
        mapping. This method does exactly that."""

        if not self.state[prop]:
            self.state[prop] = {which : val}
        else:
            self.state[prop].update({which : val})

        if self.sync_through and sync:
            self.save()

    ## Dependent on sync state between a pair of PIMDs. Each call has to
    ## include two letter dbids. Invalid field access will throw a
    ## GoutConfigError exeption. ss in the method names stands for
    ## 'sync_state'

    def _get_prop_ss (self, db1id, db2id, key):
        dbs = ('%s%s%s' % (db1id, self.get_label_separator(), db2id))
        try:
            return self.state['sync_state'][dbs][key]
        except KeyError, e:
            dbs = ('%s%s%s' % (db2id, self.get_label_separator(), db1id))
            try:
                return self.state['sync_state'][dbs][key]
            except KeyError, e:
                raise GoutConfigError(('Invalid Config read: %s'
                                       % (('%s:%s') % (dbs, key))))

    def _set_prop_ss (self, db1id, db2id, key, val, sync=True):
        dbs = '%s%s%s' % (db1id, self.get_label_separator(), db2id)
        try:
            self.state['sync_state'][dbs].update({key : val})
            if self.sync_through and sync:
                self.save()
        except KeyError, e:
            raise GoutConfigError(('Invalid Config write: %s'
                                   % (('%s:%s') % (dbs, key))))

    def get_curr_time (self):
        return iso8601.tostring(time.time())

    ##
    ## get routines for 'readonly' config settings; so they don't have a
    ## corresponding set method
    ##

    def get_olsync_guid (self):
        return self._get_prop('olsync_guid')

    def get_olsync_gid (self, which=None):
        ret = self._get_prop('olsync_gid')
        if not which:
            return ret

        return ret[which]

    def get_label_separator (self):
        return self._get_prop('label_separator')

    ##
    ## get-set pairs for application modifiable config/state and not dependent
    ## on specific PIMDB.
    ##

    def get_file_version (self):
        return self._get_prop('file_version')

    def set_file_version (self, val, sync=True):
        return self._set_prop('file_version', val, sync)

    def get_label_prefix (self):
        return self._get_prop('label_prefix')

    def set_label_prefix (self, val, sync=True):
        return self._set_prop('label_prefix', val, sync)

    ##
    ## get-set pairs for application modifiable config/state specific to a
    ## pair of synching PIMDBs..
    ##

    def get_last_sync_start (self, db1id, db2id):
        return self._get_prop_ss(db1id, db2id, 'last_sync_start')

    def set_last_sync_start (self, db1id, db2id, val=None, sync=True):
        if not val:
            val = iso8601.tostring(time.time())
        return self._set_prop_ss(db1id, db2id, 'last_sync_start', val, sync)

    def get_last_sync_stop (self, db1id, db2id):
        return self._get_prop_ss(db1id, db2id, 'last_sync_stop')

    def set_last_sync_stop (self, db1id, db2id, val=None, sync=True):
        if not val:
            val = iso8601.tostring(time.time())
        return self._set_prop_ss(db1id, db2id, 'last_sync_stop', val, sync)

    def get_sync_dir (self, db1id, db2id):
        val = self._get_prop_ss(db1id, db2id, 'sync_dir')
        if not val in sync_dirs:
            ## Check the reverse as well... Perhaps we should do this for all
            ## the get_* Hm...
            raise GoutConfigError(
                ('Invalid value for sync_dir: %s%s%s[sync_dir]: %s' %
                 (db1id, self.get_label_separator(),
                  db2id, val)))

        return val

    def set_sync_dir (self, db1id, db2id, val, sync=True):
        if not val in sync_dirs:
            raise GoutConfigError(
                ('Invalid value for sync_dir: %s%s%s[sync_dir]: %s' %
                 (db1id, self.get_label_separator(), db2id, val)))

        return self._set_prop_ss(db1id, db2id, 'sync_dir', val, sync)

    def get_conflict_resolve (self, db1id, db2id):
        val = self._get_prop_ss(db1id, db2id, 'conflict_resolve')
        if not val in [db1id, db2id]:
            raise GoutConfigError(
                ('Invalid value for: %s%s%s[conflict_resolve]: %s' %
                 (db1id, self.get_label_separator(), db2id, val)))

        return val

    def set_conflict_resolve (self, db1id, db2id, val, sync=True):
        if not val in [db1id, db2id]:
            raise GoutConfigError(
                ('Invalid value for: %s%s%s[conflic_resolve]: %s' %
                 (db1id, self.get_label_separator(), db2id, val)))

        return self._set_prop_ss(db1id, db2id, 'conflict_resolve', val, sync)


    def get_db_config (self, dbid):
        return self._get_prop('db_config')[dbid]

    def set_db_config (self, dbid, val, sync=True):
        """dbid should be a two letter dbid specifier. val should be any db
        specific config, typically a dictionary itself. Take a look at
        app_state.json.example for the sort of stuff that can be set here.

        This routine can be called to update an existing db specific config -
        in which case the entire value will be overwritten, or it can be
        invoked to set something for a new db specifier.
        """

        self._update_prop('db_config', dbid, val, sync)

    def get_group_ids (self, db1id, db2id, db, fname):
        """Return the full map of Labels to Label/Group IDs for the requested
        PIMDB. Essentially, this is used to query the identifiers used to
        track the sync status of individual entries in the database by
        labels. The caller will then have to find the label for the specific
        group he is interested in."""

        group_ids = self._get_prop_ss(db1id, db2id, 'group_ids')
        return group_ids[db][fname]

    def set_group_ids (self, db1id, db2id, db, fname, val, sync=True):
        """val should be a dictionary of type {"label" : "value"} which will
        be appended to the right group_ids dictionary"""

        group_ids = self._get_prop_ss(db1id, db2id, 'group_ids')
        group_ids[db].update({fname : val})
        self._set_prop_ss(db1id, db2id, 'group_ids', group_ids, sync)

    def save (self, fn=None):
        """fn should be the full absolute path. There is no guarantee
        where it might ge created if you are not careful."""

        if not fn:
            fn = self.fn

        try:
            fi = open(fn, "w")
        except IOError, e:
            logging.critical('Error! Could not Open file (%s): %s', fn, e)
            return

        fi.write(demjson.encode(self.state, compactly=False))

        fi.close()
