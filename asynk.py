#!/usr/bin/python
##
## Created :Tue Apr 10 15:55:20 IST 2012
##
## Copyright (C) 2012, 2013 Sriram Karra <karra.etc@gmail.com>
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

import argparse, datetime, logging, os, platform
import netrc, re, shutil, string, sys, traceback

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

## Some Global Variables to get started
asynk_ver = 'v0.4.1+'

class AsynkParserError(Exception):
    pass

class AsynkError(Exception):
    pass

class AsynkInternalError(Exception):
    pass

def main (argv=sys.argv):
    parser  = setup_parser()
    uinps = parser.parse_args()

    # Make the user directory if it does not exist
    if not os.path.exists(uinps.user_dir):
        print 'Creating ASynK User directory at: ', uinps.user_dir
        os.makedirs(uinps.user_dir)

    # If there is no config file, then let's copy something that makes
    # sense...
    if not os.path.isfile(os.path.join(uinps.user_dir, 'state.json')):
        # Let's first see if there is anything in the asynk source root
        # directory - this would be the case with early users of ASynK when
        # there was no support for a user-level config dir in ~/.asynk/
        if os.path.isfile(os.path.join(ASYNK_BASE_DIR, 'state.json')):
            shutil.copy2(os.path.join(ASYNK_BASE_DIR, 'state.json'),
                         os.path.join(uinps.user_dir, 'state.json'))
            print 'We have copied your state.json to new user directory: ',
            print uinps.user_dir
            print 'We have not copied any of your logs and backup directories.'
        else:
            ## Looks like this is a pretty "clean" run. So just copy the
            ## state.init file to get things rolling
            shutil.copy2(os.path.join(ASYNK_BASE_DIR, 'state.init.json'),
                         os.path.join(uinps.user_dir, 'state.json'))            

    # Now copy the config.json file as well.
    if not os.path.isfile(os.path.join(uinps.user_dir, 'config.json')):
            shutil.copy2(os.path.join(ASYNK_BASE_DIR, 'config.json'),
                         os.path.join(uinps.user_dir, 'config.json'))

    state_filen = os.path.join(uinps.user_dir, 'state.json')
    conf_filen  = os.path.join(uinps.user_dir, 'config.json')

    config =  Config(conf_filen, state_filen)
    config.set_user_dir(uinps.user_dir)

    setup_logging(config)
    logging.debug('Command line: "%s"', ' '.join(sys.argv))

    try:
        asynk = Asynk(uinps, config)
    except AsynkParserError, e:
        logging.critical('Error in User input: %s', e)
        quit()

    asynk.dispatch()

def setup_logging (config):
    """Set up the logging settings to the defaults. The log directory is
    created inside asynk_user_dir, which is assumed to exist already"""

    formatter = logging.Formatter('[%(asctime)s.%(msecs)03d '
                                  '%(levelname)8s] %(message)s',
                                  datefmt='%H:%M:%S')

    ## First the console logger - the logging level may be changed later after
    ## the command line arguments are parsed properly.

    global consoleLogger

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    consoleLogger = logging.StreamHandler()
    consoleLogger.setLevel(logging.INFO)
    consoleLogger.setFormatter(formatter)
    logger.addHandler(consoleLogger)

    ## Now the more detailed debug logs which are written to file in a default
    ## logs/ directory. The location of the directory is read from the
    ## configuration file.

    logdir = os.path.join(config.get_user_dir(), config.get_log_dir())
    if not os.path.exists(logdir):
        logging.info('Creating Logs directory at: %s', logdir)
        os.mkdir(logdir)

    stamp   = string.replace(str(datetime.datetime.now()), ' ', '.')
    stamp   = string.replace(stamp, ':', '-')
    logname = os.path.abspath(os.path.join(logdir, 'asynk_logs.' + stamp))
    logging.info('Debug logging to file: %s', logname)

    fileLogger = logging.FileHandler(logname, 'w')
    fileLogger.setLevel(logging.DEBUG)
    fileLogger.setFormatter(formatter)
    logger.addHandler(fileLogger)

def clear_old_log_files (config):
    logdir = os.path.join(config.get_user_dir(), config.get_log_dir())
    if not os.path.exists(logdir):
        return

    period = config.get_log_hold_period()
    logging.info('Deleting log files older than %d days, if any...', period)
    utils.del_files_older_than(logdir, period)
    logging.info('Deleting log files older than %d days, if any...done',
                 period)    

def setup_parser ():
    p = argparse.ArgumentParser(description='ASynK: PIM Awesome Sync by Karra')
    p.add_argument('--dry-run', action='store_true',
                   help='Do not sync, but merely show what will happen '
                   'if a sync is performed.')
    
    p.add_argument('--sync-all', action='store_true',
                   help='when used with --op=sync, this will ignore previous '
                   'synchronization state, and perform a complete resync.')

    p.add_argument('--op', action='store',
                   choices=('list-folders',
                            'create-folder',
                            'create-store',
                            'show-folder',
                            'del-folder',
                            'list-profiles',
                            'create-profile',
                            # 'show-profile',
                            'del-profile',
                            # 'print-item',
                            # 'del-item',
                            'sync',
                            # 'startweb',
                            'clear-sync-artifacts',),
                    default='startweb',
                    help='Specific management operation to be performed.')

    p.add_argument('--user-dir', action='store',
                   default=os.path.expanduser('~/.asynk'),
                   help=('Directory to store ASynK config files, logs ' +
                         'directory, BBDB backups directory, etc.'))
    p.add_argument('--db',  action='store', choices=('bb', 'gc', 'ol'),
                   nargs='+',
                   help=('DB IDs required for most actions. ' +
                         'Some actions need two DB IDs - do it with two --db ' +
                         'flags. When doing so remember that order might be ' + 
                         'important for certain operations.'))
    p.add_argument('--store', action='store', nargs='+',
                    help=('Specifies store ID(s) to be operated on.'))
    p.add_argument('--folder', action='store', nargs='+',
                     help='For operations that need folder ids, this option '
                     'specifies them. More than one can be specified separated '
                     'by spaces')
    p.add_argument('--item', action='store',
                     help='For Item operations specify the ID of the '
                     'Item to operate on.')

    p.add_argument('--name', action='store',
                   help=('For profile operations, specifies profile name. '
                         'For Folder operations, specifies folder name'))

    p.add_argument('--direction', action='store', default=None,
                   choices=('1way', '2way'),
                   help='Specifies whether a sync has to be unidirectional '
                   'or bidirectional. Defaults to bidirectional sync, i.e. '
                   '"2way"')

    p.add_argument('--label-regex', action='store',
                   help='A regular expression for sync artification to be '
                   'cleared from specified folder. This is to be used '
                   'independently of any sync profile.')

    p.add_argument('--conflict-resolve', action='store',
                   help='Specifies how to deal with conflicts in case of '
                   'a bidirectional sync and an item is modified in both '
                   'places. value should be one of the two dbids that are '
                   'already specified.')

    # A Group for BBDB stuff
    gg = p.add_argument_group('Google Authentication')
    gg.add_argument('--pwd', action='store', 
                   help=('Google password. Relevant only if --db=gc is used. '
                         'If this option is not specified, user is prompted '
                         'password from stdin'))


    # gw = p.add_argument_group('Web Parameters')
    # gw.add_argument('--port', action='store', type=int,
    #                 help=('Port number on which to start web server.'))

    p.add_argument('--log', action='store',
                   choices=('debug', 'info', 'error', 'critical'),
                   default='info', help='Specify level of console '
                   'logging. Note that DEBUG level logs are always written to '
                   'a log file for tracking purposes')

    p.add_argument('--version', action='version',
                   version='%(prog)s ' + ('%s' % asynk_ver))

    return p

class Asynk:
    def __init__ (self, uinps, config):
        """uinps is a Namespace object as returned from the parse_args()
        routine of argparse module."""

        level = string.upper(uinps.log)
        if level and level != 'INFO':
            consoleLogger.setLevel(getattr(logging, level))

        self.reset_fields()
        self.validate_and_snarf_uinps(uinps)

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
        mach = 'gc_%s' % pname

        ## For gmail authentication credentials, the password can be provided
        ## in a variety of ways; in the order of priority: a) on the command
        ## line b) in the ~/.netrc file where the machine name is derived from
        ## the profile name (more on this later), and finally c) from keyboard
        n = None
        netrc_user = None
        netrc_pass = None

        if 'gc' in [self.get_db1(), self.get_db2()]:
            # Use the netrc as a backup in case userid / pwd are not provided
            try:
                n = netrc.netrc()
                if mach in n.hosts.keys():
                    netrc_user, netrc_a, netrc_pass = n.authenticators(mach)
            except IOError, e:
                logging.debug('~/.netrc not found.')

            gcuser = self.get_store_id('gc')
            if not gcuser:
                if netrc_user:
                    gcuser = netrc_user
                while not gcuser:
                    gcuser = raw_input('Please enter your username: ')
                self.add_store_id('gc', gcuser)

            self.set_gcuser(gcuser)

            if self.get_gcpw():
                logging.debug('Using command line gmail password for logging in')

            while not self.get_gcpw():
                if netrc_pass and self.get_gcuser() == netrc_user:
                    self.set_gcpw(netrc_pass)
                else:
                    logging.debug('Either netrc did not have credentials for '
                                  ' User (%s) or has different login', gcuser)
                    self.set_gcpw(raw_input('Password: '))
                    if not self.get_gcpw():
                        print 'Password cannot be blank'

        db1id = self.get_db1()
        db2id = self.get_db2()

        if db1id:
            login_func = 'login_%s' % db1id
            self.set_db(db1id, getattr(self, login_func)())

            if pname and conf.profile_exists(pname):
                if not conf.get_stid1(pname):
                    conf.set_stid1(pname, self.get_store_id(db1id))

                if not conf.get_fid1(pname):
                    deff = self.get_db(db1id).get_def_folder()
                    conf.set_fid1(pname, deff.get_itemid())

        if db2id:
            login_func = 'login_%s' % db2id
            self.set_db(db2id, getattr(self, login_func)())

            if pname and conf.profile_exists(pname):
                if not conf.get_stid2(pname):
                    conf.set_stid2(pname, self.get_store_id(db2id))

                if not conf.get_fid2(pname):
                    deff = self.get_db(db2id).get_def_folder()
                    conf.set_fid2(pname, deff.get_itemid())

        self.logged_in = True
            
    def reset_fields (self):
        self.atts = {}

        self.set_db()
        self.set_db('bb', None)
        self.set_db('gc', None)
        self.set_db('ol', None)

        self.set_db1(None)
        self.set_db2(None)

        ## More to come here...

    def validate_and_snarf_uinps (self, uinps):
        # Most of the validation is already done by argparse. This is where we
        # will do some additional sanity checking and consistency enforcement,
        # mutual exclusion and so forth. In addition to this, every command
        # will do some parsing and validation itself.

        op  = 'op_' + string.replace(uinps.op, '-', '_')
        self.set_op(op)

        # Let's start with the db flags
        if uinps.db:
            if len(uinps.db) > 2:
                raise AsynkParserError('--db takes 1 or 2 arguments only')
    
            self.set_db1(uinps.db[0])
            self.set_db2(uinps.db[1] if len(uinps.db) > 1 else None)
        else:
            # Only one operation does not need a db. Check for this and move
            # on.
            if not ((self.get_op() in ['op_startweb', 'op_sync']) or 
                    (re.search('_profile', self.get_op()))):
                raise AsynkParserError('--db needed for this operation.')

        # The validation that follows is only relevant for command line
        # usage.

        if self.get_op() == 'op_startweb':
            return

        self.set_dry_run(uinps.dry_run)
        self.set_sync_all(uinps.sync_all)
        self.set_name(uinps.name)

        if uinps.store:
            temp = {}
            if len(uinps.store) >= 1:
                temp.update({self.get_db1() : uinps.store[0]})

            if len(uinps.store) >= 2:
                temp.update({self.get_db2() : uinps.store[1]})

            self.set_store_ids(temp)
        else:
            self.set_store_ids({})

        self.set_name(uinps.name)

        if uinps.folder:
            temp = {}
            if len(uinps.folder) >= 1:
                temp.update({self.get_db1() : uinps.folder[0]})

            if len(uinps.folder) >= 2:
                temp.update({self.get_db2() : uinps.folder[1]})

            self.set_folder_ids(temp)
        else:
            self.set_folder_ids(None)

        if uinps.direction:
            d = 'SYNC1WAY' if uinps.direction == '1way' else 'SYNC2WAY'
        else:
            d = None

        self.set_sync_dir(d)
        self.set_label_re(uinps.label_regex)
        self.set_conflict_resolve(uinps.conflict_resolve)
        self.set_item_id(uinps.item)
        self.set_gcpw(uinps.pwd)
        # self.set_port(uinps.port)

    def dispatch (self):
        if not self.is_dry_run():
            clear_old_log_files(self.get_config())

        res = getattr(self, self.get_op())()
        return res

    def op_create_store (self):
        if self.get_db2() != None or not (self.get_db1() in ['bb']):
            raise AsynkParserError('--create-store only supported for bb now')

        if not self.get_store_id('bb'):
            raise AsynkParserError('--create-store needs --store option '
                                   'with value with filename of BBDB file '
                                   'to be created.')

        BBPIMDB.new_store(self.get_store_id('bb'))

    def op_list_folders (self):
        self._login()
        for db in [self.get_db1(), self.get_db2()]:
            if not db:
                continue
            logging.info('Listing all folders in PIMDB %s...', db)
            self.get_db(db).list_folders()
            logging.info('Listing all folders in PIMDB %s...done', db)

    def op_create_folder (self):
        ## Let's start with some sanity checking of arguments

        # We need to have a --name flag specified
        fname = self.get_name()
        if not fname:
            raise AsynkParserError('--create-folder needs a folder name '
                                   'through --name')

        # There should only be one DB specified
        if self.get_db2():
            raise AsynkParserError('Please specify only 1 db with --db '
                                   'where new folder is to be created')

        storeid = self.get_store_id(self.get_db1())

        self._login()

        db = self.get_db(self.get_db1())
        fid = db.new_folder(fname, Folder.CONTACT_t, storeid)
        return fid

    def op_show_folder (self):
        # There should only be one DB specified
        if self.get_db2():
            raise AsynkParserError('Please specify only 1 db with --db ')

        dbid = self.get_db1()
        fid  = self.get_folder_id(dbid)

        if not fid and not ('bb' == dbid):
            raise AsynkParserError('--show-folder needs a --folder-id option')

        self._login()

        db = self.get_db(dbid)
        db.show_folder(fid)

    def op_del_folder (self):
        # There should only be one DB specified
        if self.get_db2():
            raise AsynkParserError('Please specify only 1 db with --db '
                                   'where new folder is to be created')

        dbid = self.get_db1()
        store = self.get_store_id(dbid)
        fid  = self.get_folder_id(dbid)

        if not fid and not ('bb' == dbid):
            raise AsynkParserError('--del-folder needs a --folder-id option')

        self._login()

        db = self.get_db(dbid)
        db.del_folder(fid, store)

    def op_list_profiles (self):
        self.get_config().list_profiles()

    def op_create_profile (self):
        conf = self.get_config()

        ## Do some checking to ensure the user provided all the inputs we need
        ## to process a create-profile operation
        db1 = self.get_db1()
        db2 = self.get_db2()
                           
        if None in [db1, db2]:
            raise AsynkParserError('--create-folder needs two PIMDB IDs to be '
                                   'specified.')
        
        sid1 = self.get_store_id(db1)
        sid2 = self.get_store_id(db2)

        fid1 = self.get_folder_id(db1)
        fid2 = self.get_folder_id(db2)

        if None in [fid1, fid2]:
            raise AsynkParserError('--create-folder needs two Folders IDs to be '
                                   'specified with --folder-id.')

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

        cr = self.get_conflict_resolve()
        if (not cr):
           cr = db1
        else:
           if (not cr in [db1, db2]):
               raise AsynkParserError('--conflict-resolve should be one of '
                                      'the two dbids specified earlier.')

        sync_dir = self.get_sync_dir()

        if 'ol' in [db1, db2]:
            olgid = conf.get_ol_next_gid(db1 if 'ol' == db2 else db2)
        else:
            olgid = None            

        profile = conf.get_profile_defaults()
        profile.update(
            {'coll_1' : {
                'dbid' : db1,
                'stid' : sid1,
                'foid' : fid1,
                },
             'coll_2' :  {
                'dbid' : db2,
                'stid' : sid2,
                'foid' : fid2,
                },
             'olgid'            : olgid,
             'sync_dir'         : sync_dir,
             'conflict_resolve' : cr,
             })

        conf.add_profile(pname, profile)
        logging.info('Successfully added profile: %s', pname)

    def op_show_profile (self):
        ## For now there is no need for something separate from list_profiles
        ## above(). This will eventually show sync statistics, what has
        ## changed in each folder, and so on.
        logging.info('%s: Not Implemented', 'show_profile')

    def op_del_profile (self):
        """This deletes the sync profile from the system, and clears up the
        sync state on both folders in the profile. Optionally, you can also
        delete the folders as well. If you do not wish to clear the sync state
        or delete the folders, but only want to remove the profile itself from
        the state.json, the easiest way is to edit that file by hand and be
        done with it."""

        conf     = self.get_config()
        pname    = self._load_profile(login=False)
        profiles = conf.get_profiles()

        if not pname in profiles:
            logging.info('Profile %s not in system. Nothing to do.')
            return

        self._login()

        dbid_re  = conf.get_dbid_re()
        prefix   = conf.get_label_prefix()
        sep      = conf.get_label_separator()

        label_re = '%s%s%s%s%s' % (prefix, sep, pname, sep, dbid_re)

        ## First remove the tags for the profile from both folders
        db1    = self.get_db(self.get_db1())
        f1, t  = db1.find_folder(conf.get_fid1(pname))
        hr = f1.bulk_clear_sync_flags(label_re=label_re)

        db2 = self.get_db(self.get_db2())
        f2, t  = db2.find_folder(conf.get_fid2(pname))
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
            conf.set_last_sync_start(pname, val="1980-01-01T00:00:00.00+00:00")
            conf.set_last_sync_stop(pname, val="1980-01-01T00:00:00.00+00:00")

        sync = Sync(conf, pname, self.get_db(), dr=self.is_dry_run())
        if self.is_dry_run():
            sync.prep_lists(self.get_sync_dir())
            # Since it is only a dry run, resetting to the timestamps to the
            # real older sync is sort of called for.
            conf.set_last_sync_start(pname, val=startt_old)
            conf.set_last_sync_stop(pname, val=stopt_old)
            logging.debug('Rest last sync timestamps to real values')
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

        if not pname in ['defgcol', 'defgcbb']:
            conf.set_default_profile(pname)

        return True

    def op_startweb (self):
        logging.info('Try `python asynk.py -h` for options')

    def op_clear_sync_artifacts (self):
        db1 = self.get_db1()

        self._login()

        fid = self.get_folder_id(db1)
        if db1 == 'bb' and fid == None:
            fid = 'default'

        f1, t  = self.get_db(db1).find_folder(fid)
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

    def set_db (self, dbid=None, val=None):
        if not dbid:
            self.dbs = {}
        else:
            self.dbs.update({dbid : val})

    def get_db (self, dbid=None):
        if not dbid:
            return self.dbs

        if dbid in self.dbs:
            return self.dbs[dbid]

    def get_db1 (self):
        return self._get_att('db1')

    def set_db1 (self, val):
        return self._set_att('db1', val)

    def get_db2 (self):
        return self._get_att('db2')

    def set_db2 (self, val):
        return self._set_att('db2', val)
        
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

    def set_folder_ids (self, val):
        """val should be a dictionary of dbid : folderid pairs."""
        return self._set_att('folder_id', val)

    def get_folder_id (self, dbid):
        try:
            return self._get_att('folder_id')[dbid]
        except TypeError, e:
            return None
        except KeyError, e:
            return None

    def set_store_ids (self, val):
        """val should be a dictionary of dbid : folderid pairs."""
        return self._set_att('store_id', val)

    def add_store_id (self, dbid, sid):
        return self._update_att('store_id', dbid, sid)

    def get_store_id (self, dbid):
        try:
            return self._get_att('store_id')[dbid]
        except TypeError, e:
            return None
        except KeyError, e:
            return None

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

    def get_gcuser (self):
        return self._get_att('gcuser')

    def set_gcuser (self, val):
        return self._set_att('gcuser', val)

    def get_gcpw (self):
        return self._get_att('gcpw')

    def set_gcpw (self, val):
        return self._set_att('gcpw', val)

    def get_port (self):
        return self._get_att('port')

    def set_port (self, val):
        return self._set_att('port', val)

    def get_config (self):
        return self._get_att('config')

    def set_config (self, val):
        return self._set_att('config', val)

    ## The login_* routines can assume that _load_profile has been invoked by
    ## this time.
    def login_bb (self):
        pname = self.get_name()
        conf = self.get_config()

        if pname:
            db1 = conf.get_profile_db1(pname)
            if db1 == 'bb':
                bbfn = conf.get_stid1(pname)
            else:
                bbfn = conf.get_stid2(pname)

        t = self.get_store_id('bb')
        if t:
            bbfn = t
        else:
            bbfn = '~/.bbdb'

        if not bbfn:
            raise AsynkError('No BBDB Store provided. Unable to initialize.')

        bb   = BBPIMDB(conf, bbfn)
        return bb

    def login_gc (self):
        try:
            pimgc = GCPIMDB(self.get_config(),
                            self.get_gcuser(), self.get_gcpw())
        except BadAuthentication:
            raise AsynkError('Invalid Google credentials. Cannot proceed.')

        return pimgc

    def login_ol (self):
        return OLPIMDB(self.get_config())

    def _get_validated_pname (self):
        conf  = self.get_config()
        pname = self.get_name()

        if not pname:
            def_pname = conf.get_default_profile()
            if not def_pname:
                # Use the defgcbb on Unix and defgcol profile on Windows
                if platform.system() == 'Windows':
                    pname = 'defgcol'
                else:
                    pname = 'defgcbb'
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

        if pname:
            self.set_name(pname)
            conf  = self.get_config()
    
            self.set_db1(conf.get_profile_db1(pname))
            self.set_db2(conf.get_profile_db2(pname))
    
            self.add_store_id(self.get_db1(), conf.get_stid1(pname))
            self.add_store_id(self.get_db2(), conf.get_stid2(pname))

            if not self.get_sync_dir():
                self.set_sync_dir(conf.get_sync_dir(pname))

            if not self.get_conflict_resolve():
                self.set_conflict_resolve(conf.get_conflict_resolve(pname))

        if login:
            self._login()

        return pname


if __name__ == "__main__":
    main()
