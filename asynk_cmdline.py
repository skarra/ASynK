##
## Created :Tue Apr 10 15:55:20 IST 2012
##
## Copyright (C) 2012, 2013, 2014 Sriram Karra <karra.etc@gmail.com>
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

import logging, os, re, string, sys

CUR_DIR           = os.path.abspath('')
ASYNK_BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
EXTRA_PATHS = [os.path.join(ASYNK_BASE_DIR, 'lib'),
               os.path.join(ASYNK_BASE_DIR, 'asynk'),]
sys.path = EXTRA_PATHS + sys.path

import argparse, utils
from   asynk_logger     import ASynKLogger
from   asynk_core       import Asynk, AsynkParserError
from   state            import Config
from   state_collection import collection_id_to_class as coll_id_class

class AsynkInternalError(Exception):
    pass

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
                            'list-profile-names',
                            'find-profile',
                            'create-profile',
                            'show-profile',
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
    p.add_argument('--db',  action='store', choices=('bb', 'gc', 'ol', 'cd', 'ex'),
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
                   'places. It should be set to 1 or 2 to specify the one '
                   'to be used; in case the dbs are unique. For e.g. if you '
                   'are synching from BBDB to Google Contacts, then you can '
                   'also specify the dbid itself (i.e. bb or gc)')

    # Google Contacts authentication
    gg = p.add_argument_group('Google Authentication')
    gg.add_argument('--gcuser', action='store', nargs='+',
                     help=('Google sername. Relevant only if --db=gc is used. '
                         'You can specify two if you are operating with 2 cd '
                         'dbs. You could also specify one from netrc and one '
                         'on the command line.  First one can optionally be '
                         '"None" (without the quotes). '
                         'If this option is not specified, user is prompted '
                         'for it from stdin if required.'))
    gg.add_argument('--gcpwd', action='store', nargs='+',
                   help=('Google password. Relevant only if --db=gc is used. '
                         'You can specify two if you are operating with 2 gc '
                         'dbs. You could also specify one from netrc and one '
                         'on the command line.  First one can optionally be '
                         '"None" (without the quotes). '
                         'If this option is not specified, user is prompted '
                         'password from stdin as required.'))

    # CardDAV server authentication
    cg = p.add_argument_group('CardDAV Server Authentication')
    cg.add_argument('--cduser', action='store', nargs='+',
                     help=('CardDAV username. Relevant only if --db=cd is used. '
                         'You can specify two if you are operating with 2 cd '
                         'dbs. You could also specify one from netrc and one '
                         'on the command line.  First one can optionally be '
                         '"None" (without the quotes). '
                         'If this option is not specified, user is prompted '
                         'for it from stdin if required.'))

    cg.add_argument('--cdpwd', action='store', nargs='+',
                     help=('CardDAV password. Relevant only if --db=cd is used. '
                         'You can specify two if you are operating with 2 cd '
                         'dbs. You could also specify one from netrc and one '
                         'on the command line.  First one can optionally be '
                         '"None" (without the quotes). '
                         'If this option is not specified, user is prompted '
                         'for it from stdin if required.'))

    # gw = p.add_argument_group('Web Parameters')
    # gw.add_argument('--port', action='store', type=int,
    #                 help=('Port number on which to start web server.'))

    p.add_argument('--log', action='store',
                   choices=('debug', 'info', 'error', 'critical'),
                   default='info', help='Specify level of console '
                   'logging. Note that DEBUG level logs are always written to '
                   'a log file for tracking purposes')

    p.add_argument('--version', action='version',
                   version='%(prog)s ' + ('%s' % utils.asynk_ver))

    return p

class AsynkBuilderC:
    """A helper class written in the Builder design pattern to build a Asynk
    class from the command line inputs and application configuration."""

    def __init__ (self, uinps, config, alogger):
        """uinps is a Namespace object as returned from the parse_args()
        routine of argparse module."""

        level = string.upper(uinps.log)
        if level:
            alogger.consoleLogger.setLevel(getattr(logging, level))

        self.asynk = Asynk(config, alogger)
        self.validate_and_snarf_uinps(uinps)

    def _snarf_store_ids (self, uinps):
        if uinps.store is None:
            return

        for i, stid in enumerate(uinps.store):
            coll = self.asynk.get_colls()[i]
            coll.set_stid(stid)

    def _snarf_auth_creds (self, uinps):
        if uinps.gcuser and len(uinps.gcuser) > 2:
            raise AsynkParserError('--gcuser takes 1 or 2 arguments only')

        if uinps.gcpwd and len(uinps.gcpwd) > 2:
            raise AsynkParserError('--gcpwd takes 1 or 2 arguments only')

        if uinps.cduser and len(uinps.cduser) > 2:
            raise AsynkParserError('--cduser takes 1 or 2 arguments only')

        if uinps.cdpwd and len(uinps.cdpwd) > 2:
            raise AsynkParserError('--cdpwd takes 1 or 2 arguments only')

        if (uinps.cdpwd and len(uinps.cdpwd) > 1 and
            uinps.gcpwd and len(uinps.gcpwd) > 1):
            raise AsynkParserError('--cdpwd and --gcpwd should together have'
                                   'only 2 values')

        if len(self.asynk.get_colls()) == 0:
            self.asynk._load_profile()

        if uinps.gcuser:
            for i, gcuser in enumerate(uinps.gcuser):
                coll = self.asynk.get_colls()[i]
                if gcuser != 'None':
                    coll.set_username(gcuser)

        if uinps.gcpwd:
            for i, gcpwd in enumerate(uinps.gcpwd):
                coll = self.asynk.get_colls()[i]
                if gcpwd != 'None':
                    coll.set_pwd(gcpwd)

        if uinps.cduser:
            for i, cduser in enumerate(uinps.cduser):
                coll = self.asynk.get_colls()[i]
                if cduser != 'None':
                    coll.set_username(cduser)

        if uinps.cdpwd:
            for i, cdpwd in enumerate(uinps.cdpwd):
                coll = self.asynk.get_colls()[i]
                if cdpwd != 'None':
                    coll.set_pwd(cdpwd)

    def _snarf_pname (self, uinps):
        if uinps.name:
            self.asynk.set_name(uinps.name)
        else:
            self.asynk.set_name(None)

    def _snarf_folder_ids (self, uinps):
        if uinps.folder:
            for i, fid in enumerate(uinps.folder):
                coll = self.asynk.get_colls()[i]
                coll.set_fid(fid)

    def _snarf_sync_dir (self, uinps):
        if uinps.direction:
            d = 'SYNC1WAY' if uinps.direction == '1way' else 'SYNC2WAY'
        else:
            d = None

        self.asynk.set_sync_dir(d)

    def validate_and_snarf_uinps (self, uinps):
        # Most of the validation is already done by argparse. This is where we
        # will do some additional sanity checking and consistency enforcement,
        # mutual exclusion and so forth. In addition to this, every command
        # will do some parsing and validation itself.

        op  = 'op_' + string.replace(uinps.op, '-', '_')
        self.asynk.set_op(op)

        self._snarf_pname(uinps)

        # Let's start with the db flags
        if uinps.db:
            if len(uinps.db) > 2:
                raise AsynkParserError('--db takes 1 or 2 arguments only')

            for dbid in uinps.db:
                coll = coll_id_class[dbid](config=self.asynk.get_config(),
                                           pname=self.asynk.get_name())
                self.asynk.add_coll(coll)
        else:
            # Only a few operations do not need a db. Check for this and move
            # on.
            if not ((self.asynk.get_op() in ['op_startweb', 'op_sync']) or
                    (re.search('_profile', self.asynk.get_op()))):
                raise AsynkParserError('--db needed for this operation.')

        # The validation that follows is only relevant for command line
        # usage.

        if self.asynk.get_op() == 'op_startweb':
            return

        self.asynk.set_dry_run(uinps.dry_run)
        self.asynk.set_sync_all(uinps.sync_all)

        self._snarf_store_ids(uinps)
        self._snarf_folder_ids(uinps)
        self._snarf_sync_dir(uinps)

        self.asynk.set_label_re(uinps.label_regex)
        self.asynk.set_conflict_resolve(uinps.conflict_resolve)
        self.asynk.set_item_id(uinps.item)

        if not self.asynk.get_op() in ['op_list_profiles',
                                       'op_list_profile_names']:
            self._snarf_auth_creds(uinps)

def main (argv=sys.argv):
    parser  = setup_parser()
    uinps = parser.parse_args()

    # Make the user directory if it does not exist
    uinps.user_dir = os.path.abspath(os.path.expanduser(uinps.user_dir))
    if not os.path.exists(uinps.user_dir):
        print 'Creating ASynK User directory at: ', uinps.user_dir
        os.makedirs(uinps.user_dir)

    config  = Config(ASYNK_BASE_DIR, uinps.user_dir)
    alogger = ASynKLogger(config)
    alogger.setup()

    logging.debug('Command line: "%s"', ' '.join(sys.argv))

    try:
        asynk = AsynkBuilderC(uinps, config, alogger).asynk
    except AsynkParserError, e:
        logging.critical('Error in User input: %s', e)
        quit()

    asynk.dispatch()

if __name__ == "__main__":
    main()
