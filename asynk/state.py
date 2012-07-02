##
## Created       : Tue Jul 19 13:54:53 IST 2011
## Last Modified : Mon Jul 02 22:46:37 IST 2012
##
## Copyright (C) 2011, 2012 Sriram Karra <karra.etc@gmail.com>
##
## This file is part of ASynK
##
## ASynK is free software: you can redistribute it and/or modify it under
## the terms of the GNU Affero General Public License as published by the
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
## There are two json files that are uesd by the application. One that
## captures static application configuration - called config.json, and another
## that help maintain dynamic sync status and state, called state.json. This
## file has code that manages both of these json files. In case you are
## wondering, at some point in the past it all resided in a single json file,
## and we are continuing to use the same handling framework...

import iso8601, demjson
import logging, os, re, time, traceback

import utils

sync_dirs = ['SYNC1WAY', 'SYNC2WAY']

class AsynkConfigError(Exception):
    pass

class Config:
    confi_curr_ver = 3

    def __init__ (self, confn, staten, sync_through=True):
        """If sync_through is True, any change to the configuration is
        immediately written back to the original disk file, otherwise
        the user has to explicitly save to disk."""

        confi   = None
        statefi = None

        self.confn  = os.path.abspath(confn)
        self.staten = os.path.abspath(staten) 
        self.sync_through = False

        try:
            confi = open(confn, "r")
        except IOError, e:
            logging.critical('Error! Could not Open file (%s): %s', confn, e)
            raise

        try:
            statei = open(staten, "r")
        except IOError, e:
            logging.critical('Error! Could not Open file (%s): %s', staten, e)
            raise

        stc = confi.read()
        sts = statei.read()

        # #  A sample profile is given in the initial distribution, that should
        # #  not be written back to the file. Do the needful.
        # if 'sample' in sts['profiles']:
        #     del sts['profiles']['sample']

        self.state = { 'state'  : demjson.decode(sts),
                       'config' : demjson.decode(stc), }

        confi.close()
        statei.close()

        if self.get_conf_file_version() < self.confi_curr_ver:
            logging.warn('config.json file version is out of date. You may '
                         'like to upgrade by pulling the latest version of '
                         'your config.json so you get additional variables '
                         'to configure. Note that this is optional and your '
                         'ASynK will continue to work as before.')

        self.set_app_root(os.path.abspath(''))
        self.sync_through = sync_through

    ##
    ## Helper routines
    ##

    ## Not dependent on sync state between a pair of PIMDs

    def _get_prop (self, group, key):
        return self.state[group][key]

    def _set_prop (self, group, key, val, sync=True):
        self.state[group][key] = val

        if self.sync_through and sync:
            if group == 'state':
                self.save_state()
            elif group == 'config':
                self.save_config()

    def _append_to_prop (self, group, key, val, sync=True):
        """In the particular property value is an array, we would like to
        append individual elements to the property value. this method does
        exactly that."""

        if not self.state[group][key]:
            self.state[group][key] = [val]
        else:
            self.state[group][key].append(val)

        if self.sync_through and sync:
            if group == 'state':
                self.save_state()
            elif group == 'config':
                self.save_config()

    def _update_prop (self, group, prop, which, val, sync=True):
        """If a particular property value is a dictionary, we would like to
        update the dictinary with a new mapping or alter an existing
        mapping. This method does exactly that."""

        if not self.state[group][prop]:
            self.state[group][prop] = {which : val}
        else:
            self.state[group][prop].update({which : val})

        if self.sync_through and sync:
            if group == 'state':
                self.save_state()
            elif group == 'config':
                self.save_config()

    ## get/set properties for specified sync profiles.Invalid field access
    ## will throw a AsynkConfigError exeption. ss in the method names stands
    ## for 'sync_state'

    def _get_profile_prop (self, profile, key):
        if not profile in self.state['state']['profiles']:
            raise AsynkConfigError('Profile %s not found in state.json'
                                   % profile) 

        try:
            return self.state['state']['profiles'][profile][key]
        except KeyError, e:
            raise AsynkConfigError(('Property %s not found in profile %s'
                                    % (key, profile)))

    def _set_profile_prop (self, profile, key, val, sync=True):
        if not profile in self.state['state']['profiles']:
            raise AsynkConfigError('Profile %s not found in state.json'
                                   % profile) 

        try:
            self.state['state']['profiles'][profile].update({key : val})
        except KeyError, e:
            raise AsynkConfigError(('Property %s not found in profile %s'
                                    % (key, profile)))

        if self.sync_through and sync:
            self.save_state()

    def get_curr_time (self):
        return iso8601.tostring(time.time())

    ##
    ## get routines for reading the Configuration settings from config.json
    ##

    def get_conf_file_version (self):
        return self._get_prop('config', 'file_version')

    def get_label_prefix (self):
        return self._get_prop('config', 'label_prefix')

    def get_label_separator (self):
        return self._get_prop('config', 'label_separator')

    def get_db_config (self, dbid):
        return self._get_prop('config', 'db_config')[dbid]

    def get_backup_dir (self):
        return self._get_prop('config', 'backup_dir')

    def get_backup_hold_period (self):
        try:
            return self._get_prop('config', 'backup_hold_period')
        except KeyError, e:
            ## Possibly due to a older version of the config.json. Silently
            ## return a default value
            return 7        

    def get_log_dir (self):
        return self._get_prop('config', 'log_dir')

    def get_log_hold_period (self):
        try:
            return self._get_prop('config', 'log_hold_period')
        except KeyError, e:
            ## Possibly due to a older version of the config.json. Silently
            ## return a default value
            return 7

    def get_profile_defaults (self):
        return self._get_prop('config', 'profile_defaults')

    def get_profile_name_re (self):
        return self._get_prop('config', 'profile_name_re')

    def get_dbid_re (self):
        return self._get_prop('config', 'dbid_re')

    def get_ol_guid (self):
        return self.get_db_config('ol')['guid']

    def get_ol_gid_base (self, which=None):
        dbc = self.get_db_config('ol')
        gid = dbc['gid_base']

        if not which:
            return gid

        return gid[which]

    def get_ol_cus_pid (self):
        return self.get_db_config('ol')['cus_pid']

    ##
    ## get-set pairs for sync state parameters in state.json
    ##

    def get_user_dir (self):
        return self._get_prop('state', 'asynk_user_dir')

    def set_user_dir (self, val, sync=False):
        return self._set_prop('state', 'asynk_user_dir', val, sync)

    def get_app_root (self):
        return self._get_prop('state', 'app_root')

    def set_app_root (self, val, sync=False):
        return self._set_prop('state', 'app_root', val, sync)

    def get_state_file_version (self):
        return self._get_prop('state', 'file_version')

    def set_state_file_version (self, val, sync=True):
        return self._set_prop('state', 'file_version', val, sync)

    def get_default_profile (self):
        return self._get_prop('state', 'default_profile')

    def set_default_profile (self, val, sync=True):
        return self._set_prop('state', 'default_profile', val, sync)

    def get_profiles (self):
        return self._get_prop('state', 'profiles')

    def set_profiles (self, val, sync=True):
        return self._set_prop('state', 'profiles', val, sync)

    def add_profile (self, pname, val, sync=True):
        return self._update_prop('state', 'profiles', pname, val, sync)

    ##
    ## get-set pairs for application modifiable config/state specific to a
    ## sync profile
    ##

    def get_coll_1 (self, profile):
        return self._get_profile_prop(profile, 'coll_1')

    def set_coll_1 (self, profile, val, sync=True):
        return self._set_profile_prop(profile, 'coll_1', val, sync)

    def get_coll_2 (self, profile):
        return self._get_profile_prop(profile, 'coll_2')

    def set_coll_2 (self, profile, val, sync=True):
        return self._set_profile_prop(profile, 'coll_2', val, sync)

    def get_profile_db1 (self, profile):
        return self.get_coll_1(profile)['dbid']

    def get_profile_db2 (self, profile):
        return self.get_coll_2(profile)['dbid']

    def get_stid1 (self, profile):
        return self.get_coll_1(profile)['stid']

    def set_stid1 (self, profile, stid, sync=True):
        coll1 = self.get_coll_1(profile)
        coll1.update({'stid' : stid})
        return self.set_coll_1(profile, coll1, sync)

    def get_stid2 (self, profile):
        return self.get_coll_2(profile)['stid']

    def set_stid2 (self, profile, stid, sync=True):
        coll2 = self.get_coll_2(profile)
        coll2.update({'stid' : stid})
        return self.set_coll_2(profile, coll2, sync)

    def get_fid1 (self, profile):
        return self.get_coll_1(profile)['foid']

    def set_fid1 (self, profile, fid, sync=True):
        coll1 = self.get_coll_1(profile)
        coll1.update({'foid' : fid})
        return self.set_coll_1(profile, coll1, sync)

    def get_fid2 (self, profile):
        return self.get_coll_2(profile)['foid']

    def set_fid2 (self, profile, fid, sync=True):
        coll2 = self.get_coll_2(profile)
        coll2.update({'foid' : fid})
        return self.set_coll_2(profile, coll2, sync)

    def get_last_sync_start (self, profile):
        return self._get_profile_prop(profile, 'last_sync_start')

    def set_last_sync_start (self, profile, val=None, sync=True):
        if not val:
            val = iso8601.tostring(time.time())
        return self._set_profile_prop(profile, 'last_sync_start', val, sync)

    def get_last_sync_stop (self, profile):
        return self._get_profile_prop(profile, 'last_sync_stop')

    def set_last_sync_stop (self, profile, val=None, sync=True):
        if not val:
            val = iso8601.tostring(time.time())
        return self._set_profile_prop(profile, 'last_sync_stop', val, sync)

    def get_sync_dir (self, profile):
        val = self._get_profile_prop(profile, 'sync_dir')
        if not val in sync_dirs:
            ## Check the reverse as well... Perhaps we should do this for all
            ## the get_* Hm...
            raise AsynkConfigError(
                ('Invalid value for sync_dir: %s[sync_dir]: %s' %
                 (profile, val)))

        return val

    def set_sync_dir (self, profile, val, sync=True):
        if not val in sync_dirs:
            raise AsynkConfigError(
                ('Invalid value for sync_dir: %s[sync_dir]: %s' %
                 (profile, val)))

        return self._set_profile_prop(profile, 'sync_dir', val, sync)

    def get_conflict_resolve (self, profile):
        val = self._get_profile_prop(profile, 'conflict_resolve')
        return val

    def set_conflict_resolve (self, profile, val, sync=True):
        db1id = self.get_profile_db1(profile)
        db2id = self.get_profile_db2(profile)

        if not val in [db1id, db2id]:
            raise AsynkConfigError(
                ('Invalid value for: %s[conflict_resolve]: %s' %
                 (profile, val)))

        return self._set_profile_prop(profile, 'conflict_resolve', val, sync)

    def get_ol_gid (self, profile):
        return self._get_profile_prop(profile, 'olgid')

    def set_ol_gid (self, profile, val, sync=True):
        return self._set_profile_prop(profile, 'olgid', val, sync)

    def get_itemids (self, pname):
        """Returns a dictionary of itemid mappsing from coll_1 to coll_2 as of
        the last successful sync """

        try:
            return self._get_profile_prop(pname, 'items')
        except AsynkConfigError, e:
            ## This path will happen when a user is upgrading from state.json
            ## version 2 to version 3. We don't really need to do anything
            ## special, thankfully.
            return {}

    def set_itemids (self, pname, itemids, sync=True):
        self._set_profile_prop(pname, 'items', itemids, sync)
        return itemids

    ##
    ## Finally the two save routines.
    ##

    def _save (self, fn, json):
        """fn should be the full absolute path. json is the json to be written
        out"""

        try:
            fi = open(fn, "w")
        except IOError, e:
            logging.critical('Error! Could not Open file (%s): %s', fn, e)
            return

        fi.write(json)
        fi.close()

    def save_state (self, fn=None):
        json = demjson.encode(self.state['state'], compactly=False)
        self._save(fn if fn else self.staten, json)

    def save_config (self, fn=None):
        logging.debug(' ==== Alert - trying to save config.json ==== ')
        return

        json = demjson.encode(self.state['config'], compactly=False)
        self._save(fn if fn else self.confn, json)

    ##
    ## Misc Routines
    ## 

    def _get_gid_lists (self):
        """Returns all the olgids used in the existing profiles. The returned
        value is organized as a dictionary, with the destination dbid as the
        key, and an array of olgids as the value."""

        profiles = self.get_profiles()

        destid = None
        ret = {}
        for pname, pval in profiles.iteritems():
            db1id = self.get_profile_db1(pname)
            db2id = self.get_profile_db2(pname)

            if db1id == 'ol':
                destid = db2id
            elif db2id == 'ol':
                destid = db1id
            else:
                continue

            gid = self.get_ol_gid(pname)

            if destid in ret:
                ret[destid].append(pname)
            else:
                ret.update({destid : [pname]})

        return ret
                
    def get_ol_next_gid (self, destid):
        base     = self.get_ol_gid_base(destid)
        try:
            gid_list = self._get_gid_lists()[destid]
        except KeyError, e:
            gid_list = []

        cnt   = len(gid_list)
        gid_c = base + cnt
        i     = 0

        while gid_c in gid_list:
            gid_c += 1
            i +=1
            if i > 5000:
                logging.info('state:get_ol_next_gid: more than 5000 iters!')

        return gid_c

    def make_sync_label (self, profile, dbid):
        """A sync label that is used in GC and BB to store the remote ID of a
        synched item."""

        pre = self.get_label_prefix()
        sep = self.get_label_separator()

        return (pre + sep + profile + sep + dbid)
    
    def parse_sync_label (self, label):
        """Parse the given sync label, which is of the form asynk:profile:ol
        and return a (profile, dbid) tuple."""

        pre = self.get_label_prefix()
        sep = self.get_label_separator()
        nre = self.get_profile_name_re()
        dre = self.get_dbid_re()

        reg =  (pre + sep + nre + sep + dre)
        res = re.match(reg, label)
        if res:
            return (res.group(1), res.group(2))
        else:
            return None

    def list_profiles (self):
        for key, val in self.get_profiles().iteritems():
            olgid = val['olgid'] if val['olgid'] else 0

            logging.info('')
            logging.info('*** Profile   : %s ***',     key)
            logging.info('  Collection 1: ')
            logging.info('    DB ID     : %s', val['coll_1']['dbid'])
            logging.info('    Store ID  : %s', val['coll_1']['stid'])
            logging.info('    Folder ID : %s', val['coll_1']['foid'])

            logging.info('  Collection 2: ')
            logging.info('    DB ID     : %s', val['coll_2']['dbid'])
            logging.info('    Store ID  : %s', val['coll_2']['stid'])
            logging.info('    Folder ID : %s', val['coll_2']['foid'])

            logging.info('  sync_start  : %s', val['last_sync_start'])
            logging.info('  sync_stop   : %s', val['last_sync_stop'])
            logging.info('  sync_dir    : %s', val['sync_dir'])
            logging.info('  confl_res   : %s', val['conflict_resolve'])
            logging.info('  olgid       : 0x%x', olgid)

    def profile_exists (self, pname):
        return pname in self.get_profiles()

    def get_db_profiles (self, i):
        """Return all the profiles that have the specified DB ID in one of the
        collections in the profile. The returned value is a dicationary of
        (pname : value) values - essentially a subset of the state.json file
        where the specified DB ID plays a part. `i' should be a two letter db
       id specifier such as bb, gc, ol."""

        ps = self.get_profiles()
        return dict([(k,v) for k, v in ps.items() if i in [v['coll_1']['dbid'],
                                                           v['coll_2']['dbid']]])

    def get_other_dbid (self, pname, dbid):
        """For specified profile, based on the dbid parameter, fetch and
        return the other dbid. Returns None if dbid is not one of the
        profiles' dbs"""

        db1 = self.get_profile_db1(pname)
        db2 = self.get_profile_db2(pname)

        if dbid == db1:
            return db2
        elif dbid == db2:
            return db1
