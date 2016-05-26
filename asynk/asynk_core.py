##
## Created: Sun Oct 05 15:20:59 IST 2014
##
## Copyright (C) 2014 Sriram Karra <karra.etc@gmail.com>
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

import logging, os, platform
import re, sys, traceback

## First up we need to fix the sys.path before we can even import stuff we
## want... Just some weirdness specific to our code layout...

CUR_DIR           = os.path.abspath('')
ASYNK_BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
EXTRA_PATHS = [os.path.join(ASYNK_BASE_DIR, 'lib'),
               os.path.join(ASYNK_BASE_DIR, 'asynk'),]
sys.path = EXTRA_PATHS + sys.path

try:
    from   pimdb_ol         import OLPIMDB
except ImportError, e:
    ## This could mean one of two things: (a) we are not on Windows, or (b)
    ## some of th relevant supporting stuff is not installed (like
    ## pywin32). these error cases are handled elsewhere, so move on.
    pass

from   sync             import Sync
from   state            import Config
from   gdata.client     import BadAuthentication
from   folder           import Folder
from   pimdb_gc         import GCPIMDB
from   pimdb_bb         import BBPIMDB
from   folder_bb        import BBContactsFolder
import utils
from   state_collection import collection_id_to_class as coll_id_class

class AsynkParserError(Exception):
    pass

class AsynkError(Exception):
    pass

class Asynk:
    def __init__ (self, config, alogger):
        self.alogger = alogger
        self.reset_fields()
        self.set_config(config)
        self.logged_in = False

    def _login (self, force=False):
        """This routine is typically invoked after the operation handler
        performs parameter checking. We do not want to invoke this in the
        constructor itself because it causes delay, and unnecessary database
        or network access even in the case there are errors on the command
        line.

        By default, this routine will not simply return without doing anything
        if there was already a successful call to this routine
        earlier and the db() dictionary is set. However if the optional force
        argument is True, a relogin is attempted and the pimdb objects are
        refreshed.
        """

        if self.logged_in and not force:
            return

        conf = self.get_config()
        pname = self.get_name()

        for coll in self.get_colls():
            coll.init_username_pwd()
            coll.login()

    def reset_fields (self):
        self.atts = {}

        self.set_dry_run(True)
        self.reset_colls()

    def dispatch (self):
        if not self.is_dry_run():
            self.alogger.clear_old_logs()

        res = getattr(self, self.get_op())()
        return res

    def op_create_store (self):
        if len(self.get_colls()) != 1:
            raise AsynkParserError('--create-store takes exactly one db')

        coll = self.get_colls()[0]
        if 'bb'!= coll.get_dbid():
            raise AsynkParserError('--create-store only supported for bb now')

        if not coll.get_stid():
            raise AsynkParserError('--create-store needs --store option '
                                   'with value with filename of BBDB file '
                                   'to be created.')

        BBPIMDB.new_store(coll.get_stid())

    def op_list_folders (self):
        self._login()
        for coll in self.get_colls():
            if not coll:
                continue
            dbid = coll.get_dbid()
            logging.info('Listing all folders in PIMDB %s...', dbid)
            coll.get_db().list_folders()
            logging.info('Listing all folders in PIMDB %s...done', dbid)

    def op_create_folder (self):
        ## Let's start with some sanity checking of arguments

        # We need to have a --name flag specified
        fname = self.get_name()
        if not fname:
            raise AsynkParserError('--create-folder needs a folder name '
                                   'through --name')

        # There should only be one DB specified
        if len(self.get_colls()) != 1:
            raise AsynkParserError('Please specify 1 (and only 1) arg with '
                                   '--db flag where new folder is to be '
                                   'created')

        coll = self.get_colls()[0]
        self._login()
        db = coll.get_db()

        return db.new_folder(fname, Folder.CONTACT_t, coll.get_stid())

    def op_show_folder (self):
        if len(self.get_colls()) != 1:
            raise AsynkParserError('Please specify only 1 db with --db '
                                   'for the show-folder operation')

        coll = self.get_colls()[0]
        dbid = coll.get_dbid()
        fid  = coll.get_fid()

        ## FIXME: These ParserErrors do not really belong in this file.
        if not fid and not ('bb' == dbid):
            raise AsynkParserError('--show-folder needs a --folder option')

        self._login()

        coll.get_db().show_folder(fid)

    def op_del_folder (self):
        if len(self.get_colls()) != 1:
            raise AsynkParserError('Please specify only 1 db with --db '
                                   'where new folder is to be created')

        coll = self.get_colls()[0]
        dbid = coll.get_dbid()
        stid = coll.get_stid()
        fid  = coll.get_fid()

        if not fid and not ('bb' == dbid):
            raise AsynkParserError('--del-folder needs a --folder option')

        self._login()

        coll.get_db().del_folder(fid, stid)

    def op_list_profiles (self):
        self.get_config().list_profiles()

    def op_list_profile_names (self):
        self.get_config().list_profile_names()

    def op_find_profile (self):
        """For a given set of two [db,st,fo], this will print the name of a
        matching profile. If there is no match, then None is printed."""

        conf = self.get_config()
        ## Do some checking to ensure the user provided all the inputs we need
        ## to process a create-profile operation
        colls = self.get_colls()
        if len(colls) != 2:
            raise AsynkParserError('--op=find-profile needs two PIMDB IDs '
                                   'to be specified.')

        ## FIXME: Commenting this out as the equivalent old code was commented
        ## out. There must be some good reason :)
        # if not colls[0].all_set() or not colls[1].all_set():
        #     raise AsynkParserError('--op=find-profile needs two sets of PIMDB IDs '
        #                            'Store IDs and Folder IDs to be specified.')

        coll1 = colls[0]
        coll2 = colls[1]

        fid1 = coll1.get_fid(cd_fix=True)
        fid2 = coll2.get_fid(cd_fix=True)

        if None in [fid1, fid2]:
            raise AsynkParserError('--op=find-profile needs two Folders IDs to be '
                                   'specified with --folder.')

        pname = conf.find_matching_pname(coll1.get_dbid(), coll1.get_stid(), fid1,
                                         coll2.get_dbid(), coll2.get_stid(), fid2)

        logging.info('Matched profile name: %s', pname)

    def op_create_profile (self):
        conf = self.get_config()

        ## Do some checking to ensure the user provided all the inputs we need
        ## to process a create-profile operation
        colls = self.get_colls()
        if len(colls) != 2:
            raise AsynkParserError('--create-profile needs two PIMDB IDs to be '
                                   'specified.')
        
        [dbid1, dbid2] = [x.get_dbid() for x in colls]
        [stid1, stid2] = [x.get_stid() for x in colls]
        [fid1,  fid2]  = [x.get_fid(cd_fix=True)  for x in colls]

        if None in [fid1, fid2]:
            raise AsynkParserError('--create-profile needs two Folders IDs to be '
                                   'specified with --folder.')

        # FIXME: Perhaps we should validate if the folder ids provided are
        # available in the respective PIMDBs, and raise an error if
        # not. Later.

        pname = self.get_name()
        if not pname:
            raise AsynkParserError('--create-profile needs a profile name to '
                                   'be specified')
        if conf.profile_exists(pname):
            raise AsynkParserError('There already exists a profile with name '
                                   '%s. Kindly retry with a different name'
                                   % pname)

        pname_re = conf.get_profile_name_re()
        res = re.search('^'+pname_re+'$', pname)
        if not res:
            raise AsynkParserError('Illegal profile name %s. Valid names '
                                   'should satisfy this regex: %s'
                                   % (pname, pname_re))

        cr = self.get_conflict_resolve()
        if (not cr):
           cr = "1"
        else:
           if (not cr in [dbid1, dbid2, "1", "2"]):
               raise AsynkParserError('--conflict-resolve should be one of '
                                      'the two dbids specified earlier or '
                                      'the numbers 1 or 2')
           if (dbid1 == dbid2 and not cr in ["1", "2"]):
               raise AsynkParserError('--conflict-resolve should be either 1 '
                                      'or 2 as both dbs are the same')

           if cr == dbid1:
               cr = "1"
           elif cr == dbid2:
               cr = "2"

        sync_dir = self.get_sync_dir()
        if not sync_dir:
            sync_dir = "SYNC2WAY"

        if 'ol' in [dbid1, dbid2]:
            olgid = conf.get_ol_next_gid(db1 if 'ol' == dbid2 else dbid2)
        else:
            olgid = None            

        profile = conf.get_profile_defaults()
        profile.update(
            {'coll_1' : {
                'dbid' : dbid1,
                'stid' : stid1,
                'foid' : fid1,
                },
             'coll_2' :  {
                'dbid' : dbid2,
                'stid' : stid2,
                'foid' : fid2,
                },
             'olgid'            : olgid,
             'sync_dir'         : sync_dir,
             'sync_state'       : None,
             'conflict_resolve' : cr,
             })

        conf.add_profile(pname, profile)
        logging.info('Successfully added profile: %s', pname)

    def op_show_profile (self):
        ## For now there is no need for something separate from list_profiles
        ## above(). This will eventually show sync statistics, what has
        ## changed in each folder, and so on.
        conf = self.get_config()
        pname = self.get_name()

        if not conf.profile_exists(pname):
            logging.error("Profile %s not found" % pname)
        else:
            conf.show_profile(pname)

    def op_del_profile (self):
        """This deletes the sync profile from the system, and clears up the
        sync state on both folders in the profile. Optionally, you can also
        delete the folders as well. If you do not wish to clear the sync state
        or delete the folders, but only want to remove the profile itself from
        the state.json, the easiest way is to edit that file by hand and be
        done with it."""

        conf     = self.get_config()
        pname    = self._load_profile(login=False)
        if pname is None:
            return

        profiles = conf.get_profiles()

        self._login()

        dbid_re  = conf.get_dbid_re()
        prefix   = conf.get_label_prefix()
        sep      = conf.get_label_separator()

        label_re = '%s%s%s%s%s' % (prefix, sep, pname, sep, dbid_re)

        colls = self.get_colls()
        [db1, db2] = [x.get_db() for x in colls]

        hr = True

        ## First remove the tags for the profile from both folders
        f1, t  = db1.find_folder(conf.get_fid1(pname))
        if f1:
            hr = f1.bulk_clear_sync_flags(label_re=label_re)

        f2, t  = db2.find_folder(conf.get_fid2(pname))
        if f2:
            hr = hr and f2.bulk_clear_sync_flags(label_re=label_re)
        
        if hr:
            del profiles[pname]
            conf.set_profiles(profiles)
            logging.info('Successfully deleted the profile %s from your '
                         'Asynk configuration.', pname)
        else:
            logging.info('Due to errors in clearing sync tags, profile '
                         '%s is not being deleted from your '
                         'Asynk configuration.', pname)

    def op_print_items (self):
        logging.info('%s: Not Implemented', 'print_items')

    def op_del_item (self):
        logging.info('%s: Not Implemented', 'del_item')

    def op_sync (self):
        conf  = self.get_config()
        pname = self._load_profile()

        startt_old = conf.get_last_sync_start(pname)
        stopt_old  = conf.get_last_sync_stop(pname)

        if self.is_sync_all():
            # This is the case the user wants to force a sync ignoring the
            # earlier sync states. This is useful when ASynK code changes -
            # and let's say we add support for synching a enw field, or some
            # such.
            #
            # This works by briefly resetting the last sync start and stop
            # times to fool the system. If the user is doing a dry run, we
            # will restore his earlier times dutifully.
            if self.is_dry_run():
                logging.debug('Temporarily resetting last sync times...')
            conf.set_last_sync_start(pname, val=utils.time_start)
            conf.set_last_sync_stop(pname, val=utils.time_start)
        sync = Sync(conf, pname, [x.get_db() for x in self.get_colls()],
                    dr=self.is_dry_run())
        if self.is_dry_run():
            sync.prep_lists(self.get_sync_dir())
            # Since it is only a dry run, resetting to the timestamps to the
            # real older sync is sort of called for.
            conf.set_last_sync_start(pname, val=startt_old)
            conf.set_last_sync_stop(pname, val=stopt_old)
            logging.debug('Reset last sync timestamps to real values')
        else:
            try:
                startt = conf.get_curr_time()
                result = sync.sync(self.get_sync_dir())
                if result:
                    conf.set_last_sync_start(pname, val=startt)
                    conf.set_last_sync_stop(pname)
                    logging.info('Updating item inventory...')
                    sync.save_item_lists()
                    logging.info('Updating item inventory...done')
                else:
                    logging.info('timestamps not reset for profile %s due to '
                                 'errors (previously identified).', pname)
            except Exception, e:
                logging.critical('Exception (%s) while syncing profile %s', 
                                 str(e), pname)
                logging.critical(traceback.format_exc())
                return False

        if not pname in ['defolbb', 'defbbbb']:
            conf.set_default_profile(pname)

        return True

    def op_startweb (self):
        logging.info('Try `python asynk.py -h` for options')

    def op_clear_sync_artifacts (self):
        colls = self.get_colls()
        if len(colls) < 1 :
            logging.error('Insufficient args for op clear-sync-artifacts.')
            return

        coll = colls[0]
        db1 = coll.get_dbid()

        self._login()

        fid = coll.get_fid()
        if db1 == 'bb' and fid == None:
            fid = 'default'

        f1, t  = coll.get_db().find_folder(fid)
        if not f1:
            logging.error('Folder with ID %s not found. Nothing to do',
                          fid)
            return
            
        lre = self.get_label_re()
        hr  = f1.bulk_clear_sync_flags(label_re=lre)

    ##
    ## Helper and other internal routines.
    ## 

    def _set_att (self, att, val):
        self.atts.update({att : val})
        return val

    def _update_att (self, att, key, val):
        self.atts[att].update({key : val})

    def _get_att (self, att):
        return self.atts[att]

    def __str__ (self):
        ret = ''

        for prop, val in self.atts.iteritems():
            ret += '%18s: %s\n' % (prop, val)

        return ret

    def reset_colls (self):
        self.colls = []

    def add_coll (self, coll):
        if not self.colls:
            self.reset_colls()

        self.colls.append(coll)

    def get_colls (self):
        return self.colls

    def get_op (self):
        return self._get_att('op')

    def set_op (self, val):
        return self._set_att('op', val)

    def set_dry_run (self, val):
        self._set_att('dry_run', val)

    def is_dry_run (self):
        return self._get_att('dry_run')

    def set_sync_all (self, val):
        return self._set_att('sync_all', val)

    def is_sync_all (self):
        return self._get_att('sync_all')

    def get_item_id (self):
        return self._get_att('item_id')

    def set_item_id (self, val):
        return self._set_att('item_id', val)

    def get_name (self):
        return self._get_att('name')

    def set_name (self, val):
        return self._set_att('name', val)

    def get_sync_dir (self):
        return self._get_att('sync_dir')

    def set_sync_dir (self, val):
        return self._set_att('sync_dir', val)

    def get_label_re (self):
        return self._get_att('label_re')

    def set_label_re (self, val):
        return self._set_att('label_re', val)

    def get_conflict_resolve (self):
        return self._get_att('conflict_resolve')

    def set_conflict_resolve (self, val):
        return self._set_att('conflict_resolve', val)

    def get_config (self):
        return self._get_att('config')

    def set_config (self, val):
        return self._set_att('config', val)

    def _get_validated_pname (self):
        conf  = self.get_config()
        pname = self.get_name()

        if not pname:
            def_pname = conf.get_default_profile()
            if not def_pname:
                # Use the defbbbb on Unix and defolbb profile on Windows
                if platform.system() == 'Windows':
                    pname = 'defolbb'
                else:
                    pname = 'defbbbb'
            elif conf.profile_exists(def_pname):
                pname = def_pname
            else:
                ## Hmm, the default profile disappeared from under us... No
                ## worries, just reset to null and move on..
                conf.set_default_profile(None)
                raise AsynkParserError('Could not find default profile to '
                                       'operate on. Please provide one '
                                       'explicitly with --profile-name '
                                       'option')

        return pname

    def _load_profile (self, login=True):
        pname = self._get_validated_pname()
        conf  = self.get_config()

        if pname:
            if not pname in conf.get_profile_names():
                raise AsynkParserError('Profile "%s" not found' % pname)

            self.set_name(pname)

            db1id = conf.get_profile_db1(pname)
            db2id = conf.get_profile_db2(pname)

            db1c = coll_id_class[db1id]
            db2c = coll_id_class[db2id]

            if len(self.colls) != 0:
                ## FIXME: this looks ugly but unless the command line flags
                ## handling is rewritten in whole hard to avoid.
                self.colls = []

            ## FIXME: Why were we not setting fid?
            self.add_coll(db1c(config=conf, stid=conf.get_stid1(pname),
                               pname=pname, colln=1))

            self.add_coll(db2c(config=conf, stid=conf.get_stid2(pname),
                               pname=pname, colln=2))

            if not self.get_sync_dir():
                self.set_sync_dir(conf.get_sync_dir(pname))

            if not self.get_conflict_resolve():
                self.set_conflict_resolve(conf.get_conflict_resolve(pname))

        if login:
            self._login()

        return pname

    def __str__ (self):
        self._load_profile(login=False)

        s = []
        s.append('Profile name: %s' % self.get_name())
        s.append('Operation : %s'   % self.get_op())
        s.append('sync_dir : %s'    % self.get_sync_dir())
        s.append('dry run : %s'     % self.is_dry_run())
        s.append('conflict resolve : %s' % self.get_conflict_resolve())
        colls = self.get_colls()
        if len(colls) > 0:
            s.append('Collection 1: %s' % self.get_colls()[0])
            s.append('Collection 2: %s' % self.get_colls()[1])

        return '\n'.join(s)
