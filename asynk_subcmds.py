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
from   asynk_init       import cmd_init

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
    gg.add_argument('--gc-user', action='store', nargs='+',
                    dest='gc_user',
                    help='Google username / account label.')
    gg.add_argument('--gc-creds-file', action='store', nargs='+',
                    dest='gc_creds_file',
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

    # iCloud authentication
    ig = p.add_argument_group('iCloud Authentication')
    ig.add_argument('--icuser', action='store', nargs='+',
                    help='iCloud Apple ID (email). Relevant only for ic databases.')
    ig.add_argument('--icpwd', action='store', nargs='+',
                    help='iCloud app-specific password.')

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
        if args.gc_user and len(args.gc_user) > index:
            val = args.gc_user[index]
            if val != 'None':
                coll.set_username(val)
        if args.gc_creds_file and len(args.gc_creds_file) > index:
            val = args.gc_creds_file[index]
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

    elif dbid == 'ic':
        if args.icuser and len(args.icuser) > index:
            val = args.icuser[index]
            if val != 'None':
                coll.set_username(val)
        if args.icpwd and len(args.icpwd) > index:
            val = args.icpwd[index]
            if val != 'None':
                coll.set_pwd(val)

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
## Asynk engine initialization helper
##

def _init_asynk (config, alogger, args, op, name=None):
    """Create and initialize an Asynk engine instance with all attributes
    set to sensible defaults. This replaces the piecemeal set_* calls
    that AsynkBuilderC.validate_and_snarf_uinps() used to perform."""

    asynk = Asynk(config, alogger)
    asynk.set_op(op)
    asynk.set_name(name)
    asynk.set_dry_run(args.dry_run)
    asynk.set_sync_all(getattr(args, 'sync_all', False))

    d = None
    if hasattr(args, 'direction') and args.direction:
        d = 'SYNC1WAY' if args.direction == '1way' else 'SYNC2WAY'
    asynk.set_sync_dir(d)

    asynk.set_conflict_resolve(
        getattr(args, 'conflict_resolve', None))
    asynk.set_label_re(
        getattr(args, 'label_regex', None))
    asynk.set_item_id(
        getattr(args, 'item', None))

    return asynk

##
## Profile subcommand handlers
##

def cmd_profile_list (args, config, alogger):
    asynk = _init_asynk(config, alogger, args, 'op_list_profiles')
    asynk.dispatch()

def cmd_profile_names (args, config, alogger):
    asynk = _init_asynk(config, alogger, args, 'op_list_profile_names')
    asynk.dispatch()

def cmd_profile_show (args, config, alogger):
    asynk = _init_asynk(config, alogger, args, 'op_show_profile',
                        name=args.name)
    asynk.dispatch()

def cmd_profile_find (args, config, alogger):
    if not args.db or len(args.db) != 2:
        raise AsynkParserError('profile find needs exactly 2 --db values')

    if not args.folder or len(args.folder) != 2:
        raise AsynkParserError('profile find needs exactly 2 --folder values')

    asynk = _init_asynk(config, alogger, args, 'op_find_profile')

    for i, dbid in enumerate(args.db):
        coll = coll_id_class[dbid](config=config, pname=asynk.get_name())
        coll.set_fid(args.folder[i])
        if args.store and len(args.store) > i:
            coll.set_stid(args.store[i])
        _apply_auth_to_coll(coll, dbid, args, index=i)
        asynk.add_coll(coll)

    asynk.dispatch()

def cmd_profile_create (args, config, alogger):
    if not args.db or len(args.db) != 2:
        raise AsynkParserError('profile create needs exactly 2 --db values')

    if not args.folder or len(args.folder) != 2:
        raise AsynkParserError('profile create needs exactly 2 --folder values')

    if not args.name:
        raise AsynkParserError('profile create needs a --name')

    asynk = _init_asynk(config, alogger, args, 'op_create_profile',
                        name=args.name)

    for i, dbid in enumerate(args.db):
        coll = coll_id_class[dbid](config=config, pname=args.name)
        coll.set_fid(args.folder[i])
        if args.store and len(args.store) > i:
            coll.set_stid(args.store[i])
        _apply_auth_to_coll(coll, dbid, args, index=i)
        asynk.add_coll(coll)

    asynk.dispatch()

def cmd_profile_delete (args, config, alogger):
    if not args.name:
        raise AsynkParserError('profile delete needs a --name')

    asynk = _init_asynk(config, alogger, args, 'op_del_profile',
                        name=args.name)
    asynk.dispatch()

##
## Sub-parser registration helpers
##

def _register_profile (sub, shared):
    """Register the 'profile' subcommand group with its sub-sub-parsers."""

    prof = sub.add_parser('profile', help='Manage sync profiles',
                          parents=[shared])
    prof_sub = prof.add_subparsers(dest='profile_cmd', title='profile commands')

    ## profile list
    p = prof_sub.add_parser('list', help='List all profiles',
                            parents=[shared])
    p.set_defaults(func=cmd_profile_list)

    ## profile names
    p = prof_sub.add_parser('names', help='List profile names only',
                            parents=[shared])
    p.set_defaults(func=cmd_profile_names)

    ## profile show
    p = prof_sub.add_parser('show', help='Show profile details',
                            parents=[shared])
    p.add_argument('--name', required=True,
                   help='Name of the profile to show')
    p.set_defaults(func=cmd_profile_show)

    ## profile find
    p = prof_sub.add_parser('find', help='Find a matching profile',
                            parents=[shared])
    p.add_argument('--db', nargs=2, required=True,
                   choices=['bb', 'gc', 'ol', 'cd', 'ex', 'ic'],
                   help='Two database IDs to search for')
    p.add_argument('--folder', nargs=2, required=True,
                   help='Two folder IDs to match')
    p.add_argument('--store', nargs='+',
                   help='Store IDs (optional)')
    p.set_defaults(func=cmd_profile_find)

    ## profile create
    p = prof_sub.add_parser('create', help='Create a new sync profile',
                            parents=[shared])
    p.add_argument('--db', nargs=2, required=True,
                   choices=['bb', 'gc', 'ol', 'cd', 'ex', 'ic'],
                   help='Two database IDs for the profile')
    p.add_argument('--folder', nargs=2, required=True,
                   help='Two folder IDs for the profile')
    p.add_argument('--name', required=True,
                   help='Name for the new profile')
    p.add_argument('--store', nargs='+',
                   help='Store IDs (optional)')
    p.add_argument('--direction', choices=('1way', '2way'),
                   help='Sync direction (default: 2way)')
    p.add_argument('--conflict-resolve',
                   help='Conflict resolution: 1, 2, or a db id')
    p.set_defaults(func=cmd_profile_create)

    ## profile delete
    p = prof_sub.add_parser('delete', help='Delete a sync profile',
                            parents=[shared])
    p.add_argument('--name', required=True,
                   help='Name of the profile to delete')
    p.set_defaults(func=cmd_profile_delete)


##
## Folders subcommand handlers
##

def cmd_folders_list (args, config, alogger):
    asynk = _init_asynk(config, alogger, args, 'op_list_folders')

    for dbid in args.db:
        coll = coll_id_class[dbid](config=config, pname=None)
        if args.store:
            idx = args.db.index(dbid)
            if idx < len(args.store):
                coll.set_stid(args.store[idx])
        _apply_auth_to_coll(coll, dbid, args,
                            index=args.db.index(dbid))
        asynk.add_coll(coll)

    asynk.dispatch()

def cmd_folders_create (args, config, alogger):
    if not args.name:
        raise AsynkParserError('folders create needs a --name')

    asynk = _init_asynk(config, alogger, args, 'op_create_folder',
                        name=args.name)

    dbid = args.db[0]
    coll = coll_id_class[dbid](config=config, pname=None)
    if args.store:
        coll.set_stid(args.store[0])
    _apply_auth_to_coll(coll, dbid, args)
    asynk.add_coll(coll)

    asynk.dispatch()

def cmd_folders_show (args, config, alogger):
    asynk = _init_asynk(config, alogger, args, 'op_show_folder')

    dbid = args.db[0]
    coll = coll_id_class[dbid](config=config, pname=None)
    if args.store:
        coll.set_stid(args.store[0])
    if args.folder:
        coll.set_fid(args.folder[0])
    _apply_auth_to_coll(coll, dbid, args)
    asynk.add_coll(coll)

    asynk.dispatch()

def cmd_folders_delete (args, config, alogger):
    asynk = _init_asynk(config, alogger, args, 'op_del_folder')

    dbid = args.db[0]
    coll = coll_id_class[dbid](config=config, pname=None)
    if args.store:
        coll.set_stid(args.store[0])
    if args.folder:
        coll.set_fid(args.folder[0])
    _apply_auth_to_coll(coll, dbid, args)
    asynk.add_coll(coll)

    asynk.dispatch()

def _register_folders (sub, shared):
    """Register the 'folders' subcommand group with its sub-sub-parsers."""

    fld = sub.add_parser('folders', help='Manage contact folders',
                         parents=[shared])
    fld_sub = fld.add_subparsers(dest='folders_cmd', title='folders commands')

    ## folders list
    p = fld_sub.add_parser('list', help='List folders in a store',
                           parents=[shared])
    p.add_argument('db', nargs='+',
                   choices=['bb', 'gc', 'ol', 'cd', 'ex', 'ic'],
                   help='Database ID(s) to list folders from')
    p.add_argument('--store', nargs='+',
                   help='Store IDs (optional, e.g. BBDB file path)')
    p.set_defaults(func=cmd_folders_list)

    ## folders create
    p = fld_sub.add_parser('create', help='Create a new folder',
                           parents=[shared])
    p.add_argument('db', nargs=1,
                   choices=['bb', 'gc', 'ol', 'cd', 'ex', 'ic'],
                   help='Database ID where the folder will be created')
    p.add_argument('--name', required=True,
                   help='Name for the new folder')
    p.add_argument('--store', nargs='+',
                   help='Store ID (optional)')
    p.set_defaults(func=cmd_folders_create)

    ## folders show
    p = fld_sub.add_parser('show', help='Show folder details',
                           parents=[shared])
    p.add_argument('db', nargs=1,
                   choices=['bb', 'gc', 'ol', 'cd', 'ex', 'ic'],
                   help='Database ID')
    p.add_argument('--folder', nargs=1,
                   help='Folder ID to show')
    p.add_argument('--store', nargs='+',
                   help='Store ID (optional)')
    p.set_defaults(func=cmd_folders_show)

    ## folders delete
    p = fld_sub.add_parser('delete', help='Delete a folder',
                           parents=[shared])
    p.add_argument('db', nargs=1,
                   choices=['bb', 'gc', 'ol', 'cd', 'ex', 'ic'],
                   help='Database ID')
    p.add_argument('--folder', nargs=1,
                   help='Folder ID to delete')
    p.add_argument('--store', nargs='+',
                   help='Store ID (optional)')
    p.set_defaults(func=cmd_folders_delete)

##
## Sync subcommand handler
##

def cmd_sync (args, config, alogger):
    asynk = _init_asynk(config, alogger, args, 'op_sync',
                        name=getattr(args, 'name', None))

    ## op_sync calls _load_profile() internally, which sets up collections
    ## from the profile config. We just need to apply any auth overrides
    ## that the user provided on the command line.
    asynk.dispatch()

def _register_sync (sub, shared):
    """Register the 'sync' top-level subcommand."""

    p = sub.add_parser('sync', help='Run a sync',
                       parents=[shared])
    p.add_argument('--name',
                   help='Profile name to sync (default: last used profile)')
    p.add_argument('--sync-all', action='store_true',
                   help='Ignore previous sync state and do a full resync')
    p.add_argument('--direction', choices=('1way', '2way'),
                   help='Override sync direction')
    p.set_defaults(func=cmd_sync)

##
## Store subcommand handlers
##

def cmd_store_create (args, config, alogger):
    asynk = _init_asynk(config, alogger, args, 'op_create_store')

    dbid = args.db[0]
    coll = coll_id_class[dbid](config=config, pname=None)
    if args.store:
        coll.set_stid(args.store[0])
    asynk.add_coll(coll)

    asynk.dispatch()

def _register_store (sub, shared):
    """Register the 'store' subcommand group."""

    sto = sub.add_parser('store', help='Manage data stores',
                         parents=[shared])
    sto_sub = sto.add_subparsers(dest='store_cmd', title='store commands')

    ## store create
    p = sto_sub.add_parser('create', help='Create a new data store',
                           parents=[shared])
    p.add_argument('db', nargs=1,
                   choices=['bb', 'gc', 'ol', 'cd', 'ex', 'ic'],
                   help='Database ID (currently only bb is supported)')
    p.add_argument('--store', nargs='+', required=True,
                   help='Path for the new store file')
    p.set_defaults(func=cmd_store_create)

##
## Clear-artifacts subcommand handler
##

def cmd_clear_artifacts (args, config, alogger):
    asynk = _init_asynk(config, alogger, args, 'op_clear_sync_artifacts')

    dbid = args.db[0]
    coll = coll_id_class[dbid](config=config, pname=None)
    if args.store:
        coll.set_stid(args.store[0])
    if args.folder:
        coll.set_fid(args.folder[0])
    _apply_auth_to_coll(coll, dbid, args)
    asynk.add_coll(coll)

    asynk.dispatch()

def _register_clear_artifacts (sub, shared):
    """Register the 'clear-artifacts' top-level subcommand."""

    p = sub.add_parser('clear-artifacts',
                       help='Clear sync artifacts from a folder',
                       parents=[shared])
    p.add_argument('db', nargs=1,
                   choices=['bb', 'gc', 'ol', 'cd', 'ex', 'ic'],
                   help='Database ID')
    p.add_argument('--folder', nargs=1,
                   help='Folder ID to clear artifacts from')
    p.add_argument('--store', nargs='+',
                   help='Store ID (optional)')
    p.add_argument('--label-regex',
                   help='Regex for sync labels to clear')
    p.set_defaults(func=cmd_clear_artifacts)

def _register_init (sub, shared):
    """Register the 'init' top-level subcommand (interactive wizard)."""

    p = sub.add_parser('init',
                       help='Interactive setup wizard - create a sync profile',
                       parents=[shared])
    p.add_argument('--db', nargs=2,
                   choices=['bb', 'gc', 'cd', 'ex', 'ic'],
                   help='Two database IDs (skip DB selection prompt)')
    p.add_argument('--folder', nargs=2,
                   help='Two folder IDs (skip folder selection prompt)')
    p.add_argument('--store', nargs='+',
                   help='Store IDs (e.g. BBDB file path, CardDAV URL)')
    p.add_argument('--name',
                   help='Profile name (skip name prompt)')
    p.add_argument('--direction', choices=('1way', '2way'),
                   help='Sync direction (default: 2way)')
    p.add_argument('--conflict-resolve',
                   help='Conflict resolution: 1, 2, or a db id')
    p.set_defaults(func=cmd_init)

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

    _register_profile(sub, shared)
    _register_folders(sub, shared)
    _register_sync(sub, shared)
    _register_store(sub, shared)
    _register_clear_artifacts(sub, shared)
    _register_init(sub, shared)

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
            sys.exit(1)
    else:
        parser.print_help()
