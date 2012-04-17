##
## Created       : Tue Jul 19 13:54:53 IST 2011
## Last Modified : Tue Apr 17 12:38:36 IST 2012
##
## Copyright (C) 2011, 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
##
## There are two json files that are uesd by the application. One that
## captures static application configuration - called config.json, and another
## that help maintain dynamic sync status and state, called state.json. This
## file has code that manages both of these json files. In case you are
## wondering, at some point in the past it all resided in a single json file,
## and we are continuing to use the same handling framework...

import iso8601, demjson
import logging, os, time, traceback

import utils

sync_dirs = ['SYNC1WAY', 'SYNC2WAY']

class AsynkConfigError(Exception):
    pass

class Config:
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
            return

        try:
            statei = open(staten, "r")
        except IOError, e:
            logging.critical('Error! Could not Open file (%s): %s', staten, e)
            return

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

    def get_profile_defaults (self):
        return self._get_prop('config', 'profile_defaults')

    def get_ol_guid (self):
        return self.get_db_config('ol')['guid']

    def get_ol_gid_base (self, which=None):
        dbc = self.get_db_config('ol')
        gid = dbc['gid_base']

        if not which:
            return gid

        return gid[which]

    ##
    ## get-set pairs for sync state parameters in state.json
    ##

    def get_state_file_version (self):
        return self._get_prop('state', 'file_version')

    def set_state_file_version (self, val, sync=True):
        return self._set_prop('state', 'file_version', val, sync)

    ##
    ## get-set pairs for application modifiable config/state specific to a
    ## sync profile
    ##

    def get_profile_db1 (self, profile):
        return self._get_profile_prop(profile, 'db1')

    def get_profile_db2 (self, profile):
        return self._get_profile_prop(profile, 'db2')

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
                ('Invalid value for: %s[conflic_resolve]: %s' %
                 (profile, val)))

        return self._set_profile_prop(profile, 'conflict_resolve', val, sync)


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
