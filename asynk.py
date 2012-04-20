##
## Created       : Tue Apr 10 15:55:20 IST 2012
## Last Modified : Fri Apr 20 16:04:14 IST 2012
##
## Copyright (C) 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under GPLv3
## 

import argparse, logging, os, re, string, sys, traceback

## First up we need to fix the sys.path before we can even import stuff we
## want... Just some weirdness specific to our code layout...

DIR_PATH    = os.path.abspath(os.path.dirname(os.path.realpath('Gout')))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'),
               os.path.join(DIR_PATH, 'tools'),]
sys.path = EXTRA_PATHS + sys.path

try:
    from   pimdb_ol         import OLPIMDB
except ImportError, e:
    ## This could mean one of two things: (a) we are not on Windows, or (b)
    ## some of th relevant supporting stuff is not installed (like
    ## pywin32). these error cases are handled elsewhere, so move on.
    print 'Skipping ImportError exception (', str(e), ')'
    pass

from   sync             import Sync
from   state            import Config
from   gdata.client     import BadAuthentication
from   folder           import Folder
from   pimdb_gc         import GCPIMDB
from   pimdb_bb         import BBPIMDB
from   folder_bb        import BBContactsFolder

## Some Global Variables to get started
asynk_ver = '0.01'

class AsynkParserError(Exception):
    pass

class AsynkError(Exception):
    pass

class AsynkInternalError(Exception):
    pass

def main ():
    parser  = setup_parser()
    uinps = parser.parse_args()
    try:
        asynk = Asynk(uinps)
    except AsynkParserError, e:
        logging.critical('Error in User input: %s', e)
        quit()

    asynk.dispatch()

def setup_parser ():
    p = argparse.ArgumentParser(description='ASynK: PIM Android Sync by Karra')
    p.add_argument('--dry-run', action='store_true',
                   help='Do not sync, but merely show what will happen '
                   'if a sync is performed.')

    p.add_argument('--op', action='store',
                   choices=('list-folders',
                            'create-folder',
                            'show-folder',
                            'del-folder',
                            'list-profiles',
                            'create-profile',
                            'show-profile',
                            'del-profile',
                            'print-item',
                            'del-item',
                            'sync',
                            'startweb',
                            'clear-sync-artifacts',),
                    default='startweb',
                    help='Specific management operation to be performed.')

    p.add_argument('--db',  action='store', choices=('bb', 'gc', 'ol'),
                   nargs='+',
                   help=('DB IDs required for most actions. ' +
                         'Some actions need two DB IDs - do it with two --db ' +
                         'flags. When doing so remember that order might be ' + 
                         'important for certain operations.'))

    p.add_argument('--remote-db', action='store', choices=('bb', 'gc', 'ol'),
                    help=('Specifies which remote db''s sync data to be ' +
                          'cleared with clear-sync-artifacts'))
    p.add_argument('--profile-name', action='store',
                   help=('For profile related operations, this option is '
                         'used to specify which one is needed'))
    p.add_argument('--store-id', action='store',
                    help=('Specifies ID of Outlook Message store. Useful with '
                          'certain operations like --create-folder'))
    p.add_argument('--folder-name', action='store', 
                     help='For folder operations specify the name of the '
                     'folder to operate on.')
    p.add_argument('--folder-id', action='store', nargs='+',
                     help='For operations that need folder ids, this option '
                     'specifies them. More than one can be specified separated '
                     'by spaces')
    p.add_argument('--item-id', action='store',
                     help='For Item operations specify the ID of the '
                     'Item to operate on.')

    p.add_argument('--direction', action='store', default='2way',
                   choices=('1way' '2way'),
                   help='Specifies whether a sync has to be unidirectional '
                   'or bidirectional. Defaults to bidiretioanl sync, i.e. '
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
    gg.add_argument('--user', action='store', 
                   help=('Google username. Relevant only if --db=gc is used. '
                         'If this option is not specified, user is prompted '
                         'for username from stdin'))
    gg.add_argument('--pwd', action='store', 
                   help=('Google password. Relevant only if --db=gc is used. '
                         'If this option is not specified, user is prompted '
                         'password from stdin'))


    # A Group for BBDB stuff
    gb = p.add_argument_group('BBDB Paramters')
    gb.add_argument('--bbdb-file', action='store', 
                    default=os.path.expanduser('~/.bbdb'),
                   help='BBDB File is --db=bb is used.')

    gw = p.add_argument_group('Web Parameters')
    gw.add_argument('--port', action='store', type=int,
                    help=('Port number on which to start web server.'))

    p.add_argument('--log', action='store',
                   choices=('debug', 'info', 'error', 'critical'),
                   default='info', help='Specify level of logging.')

    p.add_argument('--version', action='version',
                   version='%(prog)s v' + ('%s' % asynk_ver))

    return p

class Asynk:
    def __init__ (self, uinps):
        """uinps is a Namespace object as returned from the parse_args()
        routine of argparse module."""

        level = string.upper(uinps.log)
        logging.getLogger().setLevel(getattr(logging, level))

        self.reset_fields()
        self.validate_and_snarf_uinps(uinps)

        self.set_config(Config('./config.json', './state.json'))

    def _login (self):
        """This routine is typically invoked after the operation handler
        performs parameter checking. We do not want to invoke this in the
        constructor itself becuase it causes delay, and unnecessary database
        or network access even in the case there are errors on the command
        line."""

        if 'gc' in [self.get_db1(), self.get_db2()]:
            while not self.get_gcuser():
                self.set_gcuser(raw_input('Please enter your username: '))
                
            while not self.get_gcpw():
                self.set_gcpw(raw_input('Password: '))
                if not self.get_gcpw():
                    print 'Password cannot be blank'

        if self.get_db1():
            login_func = 'login_%s' % self.get_db1()
            self.set_db(self.get_db1(), getattr(self, login_func)())

        if self.get_db2():
            login_func = 'login_%s' % self.get_db2()
            self.set_db(self.get_db2(), getattr(self, login_func)())
            
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

        # The validation that followsi s only relevant for command line
        # usage.

        if self.get_op() == 'op_startweb':
            return

        self.set_bbdb_file(uinps.bbdb_file)
        self.set_dry_run(uinps.dry_run)

        self.set_remote_db(uinps.remote_db)
        self.set_profile_name(uinps.profile_name)

        if uinps.folder_name and uinps.folder_id:
            raise AsynkParserError('Only one of --folder-name or --folder-id '
                                   'can be specified.')

        self.set_store_id(uinps.store_id)
        self.set_folder_name(uinps.folder_name)

        if uinps.folder_id:
            temp = {}
            if len(uinps.folder_id) >= 1:
                temp.update({self.get_db1() : uinps.folder_id[0]})

            if len(uinps.folder_id) >= 2:
                temp.update({self.get_db2() : uinps.folder_id[1]})

            self.set_folder_ids(temp)
        else:
            self.set_folder_ids(None)

        self.set_sync_dir(uinps.direction)
        self.set_label_re(uinps.label_regex)
        self.set_conflict_resolve(uinps.conflict_resolve)
        self.set_item_id(uinps.item_id)
        self.set_gcuser(uinps.user)
        self.set_gcpw(uinps.pwd)
        self.set_port(uinps.port)

    def dispatch (self):
        res = getattr(self, self.get_op())()

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

        # We need to have a --folder-name flag specified
        fname = self.get_folder_name()
        if not fname:
            raise AsynkParserError('--create-folder needs a folder name '
                                   'through --folder-name')

        # There should only be one DB specified
        if self.get_db2():
            raise AsynkParserError('Please specify only 1 db with --db '
                                   'where new folder is to be created')

        storeid = self.get_store_id()

        self._login()

        db = self.get_db(self.get_db1())
        fid = db.new_folder(fname, Folder.CONTACT_t, storeid)
        if fid:
            logging.info('Successfully created folder. ID: %s',
                         fid)

    def op_show_folder (self):
        logging.debug('%s: Not Implemented', 'show_folder')

    def op_del_folder (self):
        # There should only be one DB specified
        if self.get_db2():
            raise AsynkParserError('Please specify only 1 db with --db '
                                   'where new folder is to be created')

        dbid = self.get_db1()
        fid  = self.get_folder_id(dbid)

        if not fid and not ('bb' == dbid):
            raise AsynkParserError('--del-folder needs a --folder-id option')

        self._login()

        db = self.get_db(dbid)
        db.del_folder(fid)

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
        
        fid1 = self.get_folder_id(db1)
        fid2 = self.get_folder_id(db2)

        if None in [fid1, fid2]:
            raise AsynkParserError('--create-folder needs two Folders IDs to be '
                                   'specified with --folder-id.')

        # FIXME: Perhaps we should validate if the folder ids provided are
        # available in the respective PIMDBs, and raise an error if
        # not. Later.

        pname = self.get_profile_name()
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
                                      'the two dbids specified ealrier.')

        sync_dir = self.get_sync_dir()
        if sync_dir == '1way':
            sync_dir = 'SYNC1WAY'
        else:
            sync_dir = 'SYNC2WAY'

        if 'ol' in [db1, db2]:
            olgid = conf.get_ol_next_gid(db1 if 'ol' == db2 else db2)
        else:
            olgid = None            

        profile = conf.get_profile_defaults()
        profile.update({'db1'              : db1,
                        'db2'              : db2,
                        'fid1'             : fid1,
                        'fid2'             : fid2,
                        'olgid'            : olgid,
                        'sync_dir'         : sync_dir,
                        'conflict_resolve' : cr,
                        })

        conf.add_profile(pname, profile)

    def op_show_profile (self):
        ## For now there is no need for something separate from list_profiles
        ## above(). This will eventually show sync statistics, what has
        ## changed in each folder, and so on.
        logging.debug('%s: Not Implemented', 'show_profile')

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
        
        ## Finally delete the profile from state.json and save the
        ## file. Perhaps we could check for sucess of the clear operations
        ## before we do this... Makes sense to implement. FIXME

        if hr:
            del profiles[pname]
            conf.set_profiles(profiles)
            logging.info('Successfully deleted the profiel %s from your '
                         'Asynk configuration.', pname)
        else:
            logging.info('Due to errors in clearing sync tags, profile '
                         '%s is not being deleted from your '
                         'Asynk configuration.', pname)

    def op_print_items (self):
        logging.debug('%s: Not Implemented', 'print_items')

    def op_del_item (self):
        logging.debug('%s: Not Implemented', 'del_item')

    def op_sync (self):
        conf  = self.get_config()
        pname = self._load_profile()

        sync = Sync(conf, pname, self.get_db())
        if self.is_dry_run():
            sync.prep_lists()
        else:
            try:
                startt = conf.get_curr_time()
                sync.sync()
                conf.set_last_sync_start(pname, val=startt)
                conf.set_last_sync_stop(pname)
            except Exception, e:
                logging.critical('Exception (%s) while syncing profile %s', 
                                 str(e), pname)
                logging.critical(traceback.format_exc())

        conf.set_default_profile(pname)

    def op_startweb (self):
        logging.debug('%s: Not Implemented', 'startweb')

    def op_clear_sync_artifacts (self):
        db1 = self.get_db1()

        self._login()

        fid = self.get_folder_id(db1)
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

    def _get_att (self, att):
        return self.atts[att]

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

    def get_bbdb_file (self):
        return self._get_att('bbdb_file')

    def set_bbdb_file (self, val):
        return self._set_att('bbdb_file', val)

    def set_dry_run (self, val):
        self._set_att('dry_run', val)

    def is_dry_run (self):
        return self._get_att('dry_run')

    def get_folder_name (self):
        return self._get_att('folder_name')

    def set_folder_name (self, val):
        return self._set_att('folder_name', val)

    def set_folder_ids (self, val):
        """val should be a dictionary of dbid : folderid pairs."""
        return self._set_att('folder_id', val)

    def get_folder_id (self, dbid):
        if dbid == 'bb':
            return BBContactsFolder.get_default_folder_id()
        else:
            try:
                return self._get_att('folder_id')[dbid]
            except TypeError, e:
                return None
            except KeyError, e:
                return None

    def get_item_id (self):
        return self._get_att('item_id')

    def set_item_id (self, val):
        return self._set_att('item_id', val)

    def get_remote_db (self):
        return self._get_att('remote_db')

    def set_remote_db (self, val):
        return self._set_att('remote_db', val)

    def get_profile_name (self):
        return self._get_att('profile_name')

    def set_profile_name (self, val):
        return self._set_att('profile_name', val)

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

    def get_store_id (self):
        return self._get_att('store_id')

    def set_store_id (self, val):
        return self._set_att('store_id', val)

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

    def login_bb (self):
        bbfn = self.get_bbdb_file()
        bb   = BBPIMDB(self.get_config(), bbfn)
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
        pname = self.get_profile_name()

        if not pname:
            def_pname = conf.get_default_profile()
            if conf.profile_exists(def_pname):
                pname = def_pname
            else:
                ## Hm, the default profile disappeared from under us... No
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

        self.set_db1(conf.get_profile_db1(pname))
        self.set_db2(conf.get_profile_db2(pname))

        if login:
            self._login()

        return pname


if __name__ == "__main__":
    main()
