##
## Created: Wed May 28 23:11:00 PDT 2026
## SPDX-FileCopyrightText: 2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
##
## Subcommand-based CLI for ASynK. This module implements the new
## `asynk.py <subcommand> [args]` interface, replacing the legacy
## `--op=verb-noun` style.
##

import argparse, logging, os, sys

CUR_DIR        = os.path.abspath('')
ASYNK_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXTRA_PATHS = [os.path.join(ASYNK_BASE_DIR, 'lib'),
               os.path.join(ASYNK_BASE_DIR, 'asynk'),]
sys.path = EXTRA_PATHS + sys.path

import utils
from   asynk_logger     import ASynKLogger
from   asynk_core       import Asynk, AsynkParserError
from   state            import Config
from   state_collection import collection_id_to_class as coll_id_class

##
## Shared parent parser
##

def _make_shared_parser ():
    """Build a parent parser with flags common to most subcommands.
    Uses add_help=False so it can be inherited without duplicate --help."""

    p = argparse.ArgumentParser(add_help=False)

    p.add_argument('--user-dir', action='store',
                   default=os.path.expanduser('~/.asynk'),
                   help=('Directory to store ASynK config files, logs '
                         'directory, BBDB backups directory, etc.'))

    p.add_argument('--log', action='store',
                   choices=('debug', 'info', 'error', 'critical'),
                   default='info',
                   help='Specify level of console logging. Note that DEBUG '
                   'level logs are always written to a log file.')

    p.add_argument('--dry-run', action='store_true',
                   help='Do not sync, but merely show what will happen '
                   'if a sync is performed.')

    p.add_argument('--version', action='version',
                   version='%(prog)s ' + ('%s' % utils.asynk_ver))

    # Google Contacts authentication
    gg = p.add_argument_group('Google Authentication')
    gg.add_argument('--gcuser', action='store', nargs='+',
                    help='Google username. Relevant only for gc databases.')
    gg.add_argument('--gcpwd', action='store', nargs='+',
                    help='Path to Google OAuth2 client secrets JSON.')

    # CardDAV server authentication
    cg = p.add_argument_group('CardDAV Server Authentication')
    cg.add_argument('--cduser', action='store', nargs='+',
                    help='CardDAV username. Relevant only for cd databases.')
    cg.add_argument('--cdpwd', action='store', nargs='+',
                    help='CardDAV password. Relevant only for cd databases.')

    # Exchange Server authentication
    eg = p.add_argument_group('Exchange Server Authentication')
    eg.add_argument('--ex-user', action='store', nargs='+',
                    help='Exchange username or account label.')
    eg.add_argument('--ex-token-cache', action='store', nargs='+',
                    help='Exchange token cache file path.')
    eg.add_argument('--ex-client-id', action='store', nargs='+',
                    help='Exchange Azure AD client ID override.')

    return p

##
## Auth helper
##

def _apply_auth_to_coll (coll, dbid, args, index=0):
    """Apply authentication credentials from parsed args to a collection
    object. Uses dbid to pick the right credential flags.

    index is the position (0-based) when multiple credentials of the same
    type are provided (e.g. two gc dbs in a profile create)."""

    if dbid == 'gc':
        if args.gcuser and len(args.gcuser) > index:
            val = args.gcuser[index]
            if val != 'None':
                coll.set_username(val)
        if args.gcpwd and len(args.gcpwd) > index:
            val = args.gcpwd[index]
            if val != 'None':
                coll.set_pwd(val)

    elif dbid == 'cd':
        if args.cduser and len(args.cduser) > index:
            val = args.cduser[index]
            if val != 'None':
                coll.set_username(val)
        if args.cdpwd and len(args.cdpwd) > index:
            val = args.cdpwd[index]
            if val != 'None':
                coll.set_pwd(val)

    elif dbid == 'ex':
        if args.ex_user and len(args.ex_user) > index:
            val = args.ex_user[index]
            if val != 'None':
                coll.set_username(val)
        if args.ex_client_id and len(args.ex_client_id) > index:
            val = args.ex_client_id[index]
            if val != 'None':
                coll.set_pwd(val)
        if args.ex_token_cache and len(args.ex_token_cache) > index:
            val = args.ex_token_cache[index]
            if val != 'None' and hasattr(coll, 'set_token_cache'):
                coll.set_token_cache(val)

##
## Config and logger bootstrap
##

def _setup_config_and_logger (args):
    """Create user directory if needed, instantiate Config and ASynKLogger.
    Returns (config, alogger) tuple."""

    user_dir = os.path.abspath(os.path.expanduser(args.user_dir))
    if not os.path.exists(user_dir):
        print('Creating ASynK User directory at: ', user_dir)
        os.makedirs(user_dir)

    config  = Config(ASYNK_BASE_DIR, user_dir)
    alogger = ASynKLogger(config)
    alogger.setup()

    level = args.log.upper()
    if level:
        alogger.consoleLogger.setLevel(getattr(logging, level))

    logging.debug('Command line: "%s"', ' '.join(sys.argv))

    return config, alogger

##
## Top-level subcommand parser and main entry point
##

def _build_parser (shared):
    """Build the top-level parser with all subcommand sub-parsers."""

    p = argparse.ArgumentParser(
        prog='asynk.py',
        description='ASynK: PIM Awesome Sync by Karra',
        parents=[shared])

    sub = p.add_subparsers(dest='subcmd', title='subcommands',
                           description='Available subcommands. '
                           'Run `asynk.py <subcommand> --help` for details.')

    ## Subcommand sub-parsers will be registered here by subsequent
    ## sub-phases. For now the parser is functional but has no
    ## subcommands yet.

    return p

def subcmd_main (argv=sys.argv):
    """Entry point for the subcommand-style CLI. Called from asynk.py
    when a subcommand is detected."""

    shared = _make_shared_parser()
    parser = _build_parser(shared)
    args   = parser.parse_args(argv[1:])

    if not args.subcmd:
        parser.print_help()
        return

    config, alogger = _setup_config_and_logger(args)

    ## Dispatch to the handler set by set_defaults(func=...) on each
    ## subcommand's sub-parser.
    if hasattr(args, 'func'):
        try:
            args.func(args, config, alogger)
        except AsynkParserError as e:
            logging.critical('Error in user input: %s', e)
    else:
        parser.print_help()
