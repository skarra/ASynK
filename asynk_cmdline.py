#!/usr/bin/python
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

import logging, os, sys

CUR_DIR           = os.path.abspath('')
ASYNK_BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
EXTRA_PATHS = [os.path.join(ASYNK_BASE_DIR, 'lib'),
               os.path.join(ASYNK_BASE_DIR, 'asynk'),]
sys.path = EXTRA_PATHS + sys.path

import argparse, utils
from   asynk_logger     import ASynKLogger
from   asynk_core       import Asynk, AsynkParserError
from   state            import Config

class AsynkError(Exception):
    pass

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
    gg.add_argument('--pwd', action='store', 
                   help=('Google password. Relevant only if --db=gc is used. '
                         'If this option is not specified, user is prompted '
                         'password from stdin'))

    # CardDAV server authentication
    cg = p.add_argument_group('CardDAV Server Authentication')
    cg.add_argument('--cduser', action='store', 
                     help=('CardDAV username. Relevant only if --db=cd is used. '
                         'If this option is not specified, user is prompted '
                         'for it from stdin'))

    cg.add_argument('--cdpwd', action='store', 
                     help=('CardDAV password. Relevant only if --db=cd is used. '
                         'If this option is not specified, user is prompted '
                         'for it from stdin'))

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
        asynk = Asynk(uinps, config, alogger)
    except AsynkParserError, e:
        logging.critical('Error in User input: %s', e)
        quit()

    asynk.dispatch()

if __name__ == "__main__":
    main()
