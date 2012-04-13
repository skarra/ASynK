##
## Created       : Tue Apr 10 15:55:20 IST 2012
## Last Modified : Fri Apr 13 14:59:20 IST 2012
##
## Copyright (C) 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under GPLv3
## 

import argparse, logging, os, string, sys, traceback

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

## Some Global Variables to get started
asynk_ver = '0.01'

class AsynkParserError(Exception):
    pass

class AsynkError(Exception):
    pass

def main ():
    parser  = setup_parser()
    uinps = parser.parse_args()
    try:
        asynk = Asynk(uinps)
    except AsynkParserError, e:
        logging.critical('Error in Uesr input: %s', e)
        quit()

    asynk.dispatch()

def setup_parser ():
    p = argparse.ArgumentParser(description='ASynK: PIM Android Sync by Karra')
    p.add_argument('--dry-run', action='store_true',
                   help='Do not sync, but merely show what will happen '
                   'if a sync is performed.')

    p.add_argument('--op', action='store',
                   choices = ('list-folders',
                              'create-folder',
                              'del-folder',
                              'list-items',
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
    p.add_argument('--store-id', action='store',
                    help=('Specifies ID of Outlook Message store. Useful with '
                          'certain operations like --create-folder'))
    p.add_argument('--folder-name', action='store', 
                     help='For folder operations specify the name of the '
                     'folder to operate on.')
    p.add_argument('--folder-id', action='store',
                     help='For folder operations specify the ID of the '
                     'folder to operate on. Only one of folder-id and '
                     'should be specified')
    p.add_argument('--item-id', action='store',
                     help='For Item operations specify the ID of the '
                     'Item to operate on.')

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
    gb.add_argument('--file', action='store', 
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

        self.set_config(Config('./app_state.json'))

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

        # Let's start with the db flags
        if uinps.db:
            if len(uinps.db) > 2:
                raise AsynkParserError('--db takes 1 or 2 arguments only')
    
            self.set_db1(uinps.db[0])
            self.set_db2(uinps.db[1] if len(uinps.db) > 1 else None)

        op  = string.replace(uinps.op, '-', '_')
        self.set_op(op)

        # The validation that followsi s only relevant for command line
        # usage.

        if self.get_op() == 'startweb':
            return

        self.set_bbdb_file(uinps.file)
        self.set_dry_run(uinps.dry_run)

        if uinps.folder_name and uinps.folder_id:
            raise AsynkParserError('Only one of --folder-name or --folder-id '
                                   'can be specified.')

        self.set_store_id(uinps.store_id)
        self.set_folder_name(uinps.folder_name)
        self.set_folder_id(uinps.folder_id)
        self.set_item_id(uinps.item_id)

        self.set_gcuser(uinps.user)
        self.set_gcpw(uinps.pwd)

        if 'gc' in [self.get_db1(), self.get_db2()]:
            while not self.get_gcuser():
                self.set_gcuser(raw_input('Please enter your username: '))
                
            while not self.get_gcpw():
                self.set_gcpw(raw_input('Password: '))
                if not self.get_gcpw():
                    print 'Password cannot be blank'

        self.set_port(uinps.port)

    def dispatch (self):
        res = getattr(self, self.get_op())()

    def list_folders (self):
        for db in [self.get_db1(), self.get_db2()]:
            if not db:
                continue
            logging.info('Listing all folders in PIMDB %s...', db)
            self.get_db(db).list_folders()
            logging.info('Listing all folders in PIMDB %s...done', db)

    def create_folder (self):
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

        if not self.get_db1():
            raise AsynkParserError('Please specify the PIMDB where new folder '
                                   'is to be created, with --db option')

        storeid = self.get_store_id()

        db = self.get_db(self.get_db1())
        db.new_folder(fname, Folder.CONTACT_t, storeid)
            

    def del_folder (self):
        logging.debug('%s; Not Implemented', 'del_folder')

    def list_items (self):
        logging.debug('%s: Not Implemented', 'list_items')

    def print_items (self):
        logging.debug('%s: Not Implemented', 'print_items')

    def del_item (self):
        logging.debug('%s: Not Implemented', 'del_item')

    def sync (self):
        logging.debug('%s: Not Implemented', 'sync')

    def startweb (self):
        logging.debug('%s: Not Implemented', 'startweb')

    def clear_sync_artifacts (self):
        logging.debug('%s: Not Implemented', 'clear_sync_artifacts')

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

    def get_db (self, dbid):
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

    def get_folder_id (self):
        return self._get_att('folder_id')

    def set_folder_id (self, val):
        return self._set_att('folder_id', val)

    def get_item_id (self):
        return self._get_att('item_id')

    def set_item_id (self, val):
        return self._set_att('item_id', val)

    def get_remote_db (self):
        return self._get_att('remote_db')

    def set_remote_db (self, val):
        return self._set_att('remote_db', val)

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

if __name__ == "__main__":
    main()
