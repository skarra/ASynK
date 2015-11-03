##
## Created : Tue Jul 19 13:54:53 IST 2011
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
## There are two json files that are uesd by the application. One that
## captures static application configuration - called config.json, and another
## that help maintain dynamic sync status and state, called state.json. This
## file has code that manages both of these json files. In case you are
## wondering, at some point in the past it all resided in a single json file,
## and we are continuing to use the same handling framework...

import iso8601, demjson
import glob, logging, os, re, shutil, sys, time, stat

sync_dirs = ['SYNC1WAY', 'SYNC2WAY']

class AsynkConfigError(Exception):
    pass

class Config:
    def __init__ (self, asynk_base_dir, user_dir, sync_through=True):
        ## FIXME: The sync_through flag does not really work as expected. The
        ## intended behaviour was this will provide a default which can be
        ## overriden in any call. The way each attribute write has been
        ## implemented, all the methods override this explicitly - basically
        ## rendering this useless, more or less. The right fix is to set the
        ## default values for 'sync' in attribute writers to this value and
        ## allow the callers to override it as required. This 'bug' has no
        ## user-facing consequences. So get to it some time.

        """If sync_through is True, any change to the configuration is
        immediately written back to the original disk file, otherwise
        the user has to explicitly save to disk."""

        self.state = { 'state'  : {},
                       'config' : {} }

        self.sync_through = False
        self.set_app_root(asynk_base_dir)
        self.set_user_dir(user_dir)

        confi   = None
        statei  = None
        self.confi_curr_ver = Config.get_latest_config_version(self.get_app_root())

        self.confpy = os.path.abspath(os.path.join(user_dir, 'config.py'))
        self.confn  = 'config_v%d.json' % self.confi_curr_ver
        self.confn  = os.path.abspath(os.path.join(asynk_base_dir,
                                                   'config', self.confn))
        self.staten = os.path.abspath(os.path.join(user_dir, 'state.json'))

        self._setup_state_json()
        self._migrate_config_if_reqd(self.confi_curr_ver)

        try:
            print 'Applying base config from file %s...' % self.confn
            confi = open(self.confn, "r")
            print 'Applying base config from file %s...done' % self.confn
        except IOError, e:
            print 'Error! Could not Open file (%s): %s' % (self.confn, e)
            raise

        try:
            statei = open(self.staten, "r")
        except IOError, e:
            print 'Error! Could not Open file (%s): %s' % (self.staten, e)
            raise

        stc = demjson.decode(confi.read())
        sts = demjson.decode(statei.read())

        print 'Applying user customizations from file %s...' % self.confpy
        self._customize_config(self.confpy, stc)
        print 'Applying user customizations from file %s...done' % self.confpy

        # #  A sample profile is given in the initial distribution, that should
        # #  not be written back to the file. Do the needful.
        # if 'sample' in sts['profiles']:
        #     del sts['profiles']['sample']

        self.state = { 'state'  : sts,
                       'config' : stc, }

        ## FIXME: A bit grotesque that we have to do this again. But let's go
        ## with this flow for now.

        self.set_app_root(asynk_base_dir)
        self.set_user_dir(user_dir)

        confi.close()
        statei.close()

        if self.get_conf_file_version() < self.confi_curr_ver:
            logging.warn('config.json file version is out of date. You may '
                         'like to upgrade by pulling the latest version of '
                         'your config.json so you get additional variables '
                         'to configure. Note that this is optional and your '
                         'ASynK will continue to work as before.')

        self.sync_through = sync_through

    ##
    ## Helper routines
    ##

    ## First some class methods

    @staticmethod
    def get_latest_config_version (root):
        d = os.path.join(root, 'config')
        files = glob.glob(os.path.join(d, 'config_*.json'))
        vers = [int(re.search('_v(\d+).json$', x).group(1)) for x in files]
        vers.sort(reverse=True)

        return vers[0]

    @staticmethod
    def get_latest_config_filen (root):
        return 'config_v%s.json' % Config.get_latest_config_version(root)

    def _setup_state_json (self):
        user_dir = self.get_user_dir()
        base_dir = self.get_app_root()

        # If there is no config file, then let's copy something that makes
        # sense...
        if not os.path.isfile(os.path.join(user_dir, 'state.json')):
            # Let's first see if there is anything in the asynk source root
            # directory - this would be the case with early users of ASynK when
            # there was no support for a user-level config dir in ~/.asynk/
            if os.path.isfile(os.path.join(base_dir, 'state.json')):
                shutil.copy2(os.path.join(base_dir, 'state.json'),
                             os.path.join(user_dir, 'state.json'))
                print 'We have copied your state.json to new user directory: ',
                print user_dir
                print 'We have not copied any of your logs and backup directories.'
            else:
                dest_state = os.path.join(user_dir, 'state.json')
                ## Looks like this is a pretty "clean" run. So just copy the
                ## state.init file to get things rolling
                shutil.copy2(os.path.join(base_dir, 'state.init.json'),
                             dest_state)
                ## Add user write permission in case state.init.json
                ## was not writable
                os.chmod(dest_state,
                         os.stat(dest_state).st_mode | stat.S_IWUSR)

    def _migrate_config_if_reqd (self, curr_ver):
        user_dir = self.get_user_dir()
        base_dir = self.get_app_root()
        confpy_init = os.path.join(base_dir, 'config', 'config.init.py')
        confpy      = os.path.join(user_dir, 'config.py')
        confjs      = os.path.join(user_dir, 'config.json')
        confjs_curr = os.path.join(base_dir, 'config',
                                   'config_v%d.json' % curr_ver)

        if not os.path.isfile(confpy):
            shutil.copy2(confpy_init, confpy)

        if os.path.isfile(confjs):
            user_config = open(confjs, 'r').read()

            user_ver = demjson.decode(user_config)['file_version']
            confjs_curr1 = os.path.join(base_dir, 'config',
                                        'config_v%d.json' % user_ver)
            std_config  = open(confjs_curr1, 'r').read()

            if user_config != std_config:
                print
                print '*** NOTE: Due to recent changes to the customization system'
                print '***       your config needs to be'
                print '***       migrated. However as you have modified your'
                print '***       configuration, auto migration is not possible'
                print '***       and we need your manual intervention.'
                print
                print '***       You need to do the following steps:'
                print
                print '***       1) delete your customization json'
                print '***       2) port your changes to the new config.py file'
                print '***          that has been copied to you asynk config dir.'
                print
                print '*** You can view the comments in config.py for ideas.'
                print '*** ASynK will now exit without doing anything more.'
                print

                sys.exit(0)
            else:
                os.remove(confjs)
                print '*** NOTE: Custom config auto migrated from v%d' % user_ver

    def _customize_config (self, confpy, config):
        user_dir = self.get_user_dir()
        sys.path += [user_dir]
        confpy_m = None
        try:
            confpy_m = __import__('config')
        except Exception, e:
            print 'Error importing config from %s: %s' % (user_dir, e)
            return

        confpy_m.customize_config(config)

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

        self.state['state']['profiles'][profile].update({key : val})

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

    def get_cd_logging (self):
        return self.get_db_config('cd')['log']

    def get_gc_logging (self):
        return self.get_db_config('gc')['log']

    def get_ex_guid (self):
        return self.get_db_config('ex')['guid']

    def get_ex_cus_pid (self):
        return self.get_db_config('ex')['cus_pid']

    def get_ex_stags_pname (self):
        return self.get_db_config('ex')['stags_pname']

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

    def get_profile_names (self):
        return self.get_profiles().keys()

    ##
    ## get-set pairs for application modifiable config/state specific to a
    ## sync profile
    ##

    ## FIXME: In all these get_set methods, profile should be renamed to pname
    ## to avoid confusion

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
        stid = None if stid == 'None' else stid
        coll1 = self.get_coll_1(profile)
        coll1.update({'stid' : stid})
        return self.set_coll_1(profile, coll1, sync)

    def get_stid2 (self, profile):
        return self.get_coll_2(profile)['stid']

    def set_stid2 (self, profile, stid, sync=True):
        stid = None if stid == 'None' else stid
        coll2 = self.get_coll_2(profile)
        coll2.update({'stid' : stid})
        return self.set_coll_2(profile, coll2, sync)

    def get_fid1 (self, profile):
        return self.get_coll_1(profile)['foid']

    def set_fid1 (self, profile, fid, sync=True):
        fid = None if fid == 'None' else fid
        coll1 = self.get_coll_1(profile)
        coll1.update({'foid' : fid})
        return self.set_coll_1(profile, coll1, sync)

    def get_fid2 (self, profile):
        return self.get_coll_2(profile)['foid']

    def set_fid2 (self, profile, fid, sync=True):
        fid = None if fid == 'None' else fid
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

        if not val in [db1id, db2id, "1", "2"]:
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

    def get_ex_sync_state (self, pname):
        return self._get_profile_prop(pname, 'sync_state')

    ## Throws an exception if the profile name does not support the sync_state
    ## flag, IOW - it if it is not an exchange profile.
    ## On success retuns sync_state input parameter
    def set_ex_sync_state (self, pname, sync_state, sync=True):
        ## Fetch the old one to force an exception if the prop is not there
        old = self.get_ex_sync_state(pname)
        self._set_profile_prop(pname, 'sync_state', sync_state, sync)
        return sync_state

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

    def _get_gid_lists (self, dbid, get_fn):
        profiles = self.get_profiles()

        destid = None
        ret = {}
        for pname, pval in profiles.iteritems():
            db1id = self.get_profile_db1(pname)
            db2id = self.get_profile_db2(pname)

            if db1id == dbid:
                destid = db2id
            elif db2id == dbid:
                destid = db1id
            else:
                continue

            gid = get_fn(pname)

            if destid in ret:
                ret[destid].append(gid)
            else:
                ret.update({destid : [gid]})

        return ret
                
    def _get_ol_gid_lists (self):
        """Returns all the olgids used in the existing profiles. The returned
        value is organized as a dictionary, with the destination dbid as the
        key, and an array of olgids as the value."""

        return self._get_gid_lists('ol', get_fn=self.get_ol_gid)

    def _get_next_gid (self, destid, base_fn, gid_lists_fn):
        base     = base_fn(destid)
        try:
            gid_list = gid_lists_fn()[destid]
        except KeyError, e:
            gid_list = []

        cnt   = len(gid_list)
        gid_c = base + cnt
        i     = 0

        while gid_c in gid_list:
            gid_c += 1
            i +=1
            if i > 5000:
                logging.info('state:get_next_gid: more than 5000 iters!')

        return gid_c

    def get_ol_next_gid (self, destid):
        return self._get_next_gid(destid=destid, base_fn=self.get_ol_gid_base,
                                  gid_lists_fn=self._get_ol_gid_lists)

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
        for key in self.get_profiles().keys():
            logging.info('')
            self.show_profile(key)

    def list_profile_names (self):
        for key in self.get_profiles().keys():
            logging.info('Profile: %s', key)

    def show_profile (self, name):
        profile = self.get_profiles()[name]

        olgid = profile['olgid'] if profile['olgid'] else 0

        logging.info('*** Profile   : %s ***', name)
        logging.info('  Collection 1: ')
        logging.info('    DB ID     : %s', profile['coll_1']['dbid'])
        logging.info('    Store ID  : %s', profile['coll_1']['stid'])
        logging.info('    Folder ID : %s', profile['coll_1']['foid'])

        logging.info('  Collection 2: ')
        logging.info('    DB ID     : %s', profile['coll_2']['dbid'])
        logging.info('    Store ID  : %s', profile['coll_2']['stid'])
        logging.info('    Folder ID : %s', profile['coll_2']['foid'])

        logging.info('  sync_start  : %s', profile['last_sync_start'])
        logging.info('  sync_stop   : %s', profile['last_sync_stop'])
        logging.info('  sync_dir    : %s', profile['sync_dir'])
        logging.info('  confl_res   : %s', profile['conflict_resolve'])
        logging.info('  olgid       : 0x%x', olgid)

    def profile_exists (self, pname):
        return pname in self.get_profiles()

    def find_matching_pname (self, db1, st1, fo1, db2, st2, fo2):
        """Return the name(s) of any existing profile for the matching tuples
        of db, store, and folder specified. Returns None if there is nothing
        matching found. As always the order matters.

        If a store id or a folder id is None, then it is used to match any
        value in those fields. If they are 'default' then the appropriate
        deafult values are matched."""

        ret = []

        ## FIXME: This is a hack. Needs to be fixed. Basically None and
        ## default are treated the same. This should not be the case.
        st1 = None if st1 in ["default", "None"] else st1
        st2 = None if st2 in ["default", "None"] else st2
        fo1 = None if fo1 in ["default", "None"] else fo1
        fo2 = None if fo2 in ["default", "None"] else fo2

        pnames = self.get_profile_names()
        for p in pnames:
            if (db1 == self.get_profile_db1(p) and
                db2 == self.get_profile_db2(p) and
                (not st1 or st1 == self.get_stid1(p)) and
                (not st2 or st2 == self.get_stid2(p)) and
                (not fo1 or fo1 == self.get_fid1(p))  and
                (not fo2 or fo2 == self.get_fid2(p))):
                ret.append(p)

        return ret if len(ret) > 0 else None

    def get_store_pnames (self, db1, db2=None, store=None):
        """Find the profile name(s) from db1:db2 where the store field matches
        'store'.

        The return value is an array of profile names.

        If db2 is None, all stores from db1 with matching store are
        returned. If store is None all pnames from db1 to db2 are returned. If
        both db2 and store are None, then all pnames from db1 are returned."""

        ps = self.get_profile_names()
        ret = []
        for k in ps:
            if db1 != self.get_profile_db1(k):
                continue
            if db2 and db2 != self.get_profile_db2(k):
                continue
            if store and store != self.get_stid1(k):
                continue

            ret.append(k)

        return ret if len(ret) > 0 else None

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
