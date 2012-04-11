##
## Created       : Tue Apr 10 15:55:20 IST 2012
## Last Modified : Wed Apr 11 15:58:22 IST 2012
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

## Some Global Variables to get started
asynk_ver = '0.01'

class AsynkParserError(Exception):
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
    gb.add_argument('--file', action='store', default='~/.bbdb',
                   help='BBDB File is --db=bb is used.')

    gw = p.add_argument_group('Web Parameters')
    gw.add_argument('--port', action='store', type=int,
                    help=('Port number on which to start web server.'))

    p.add_argument('--version', action='version',
                   version='%(prog)s v' + ('%s' % asynk_ver))

    return p

class Asynk:
    def __init__ (self, uinps):
        """uinps is a Namespace object as returned from the parse_args()
        routine of argparse module."""

        print uinps

        self.reset_fields()
        self.validate_and_snarf_uinps(uinps)

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
        # mutual exclusion and so forth.

        # Let's start with the db flags
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

        

    def dispatch (self):
        res = getattr(self, self.get_op())()

    def list_folders (self):
        logging.debug('%s: Not Implemented', 'list_folders')

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

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    main()
