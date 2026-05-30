##
## Created: Thu May 29 17:20:00 PDT 2026
## SPDX-FileCopyrightText: 2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
##
## Interactive setup wizard for ASynK. Walks the user through DB selection,
## credential setup, folder selection, and profile creation.
##

import logging, os, re, sys

CUR_DIR        = os.path.abspath('')
ASYNK_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXTRA_PATHS = [os.path.join(ASYNK_BASE_DIR, 'lib'),
               os.path.join(ASYNK_BASE_DIR, 'asynk'),]
sys.path = EXTRA_PATHS + sys.path

import utils
from   state            import Config
from   state_collection import collection_id_to_class as coll_id_class
from   state_collection import AsynkCollectionError
from   asynk_core       import Asynk, AsynkParserError
from   folder           import Folder

## DB IDs and their human-friendly names.  Outlook is excluded -- it is
## Windows-only and has a different setup path.
DB_NAMES = {
    'bb': 'BBDB (Emacs Big Brother Database)',
    'gc': 'Google Contacts',
    'ex': 'Exchange Online (Microsoft 365 / Outlook.com)',
    'cd': 'CardDAV Server (Nextcloud, Radicale, etc.)',
}

## Ordered list for the menu (most common first)
DB_ORDER = ['gc', 'ex', 'cd', 'bb']

##
## Text / UI helpers
##

def _print_banner ():
    print()
    print('=' * 60)
    print('  ASynK %s -- Interactive Setup Wizard' % utils.asynk_ver)
    print('=' * 60)
    print()
    print('  This wizard will help you set up a sync profile')
    print('  between two contact stores.')
    print()

def _prompt_choice (prompt, options, default=None):
    """Present a numbered menu and return the selected option value.

    options is a list of (value, label) tuples.
    default is an optional value that will be pre-selected if the user
    just presses Enter.
    """

    for i, (val, label) in enumerate(options, 1):
        marker = ' *' if val == default else ''
        print('  %d. %s%s' % (i, label, marker))
    print()

    default_idx = None
    if default is not None:
        for i, (val, _) in enumerate(options, 1):
            if val == default:
                default_idx = i
                break

    while True:
        suffix = ' [%d]' % default_idx if default_idx else ''
        try:
            raw = input('%s%s: ' % (prompt, suffix)).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            raise SystemExit('Setup cancelled.')

        if not raw and default_idx:
            return options[default_idx - 1][0]

        try:
            idx = int(raw)
            if 1 <= idx <= len(options):
                return options[idx - 1][0]
        except ValueError:
            pass

        print('  Please enter a number between 1 and %d.' % len(options))

def _prompt_input (prompt, default=None):
    """Prompt for a text value with an optional default."""

    suffix = ' [%s]' % default if default else ''
    try:
        raw = input('%s%s: ' % (prompt, suffix)).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise SystemExit('Setup cancelled.')

    return raw if raw else default

def _prompt_yesno (prompt, default=True):
    """Prompt for a yes/no answer.  Returns True for yes, False for no."""

    hint = 'Y/n' if default else 'y/N'
    try:
        raw = input('%s [%s]: ' % (prompt, hint)).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        raise SystemExit('Setup cancelled.')

    if not raw:
        return default
    return raw[0] == 'y'

##
## DB selection
##

def _select_dbs (args):
    """Return (db1_id, db2_id).  Uses --db if provided, otherwise prompts."""

    if args.db and len(args.db) == 2:
        db1, db2 = args.db
        print('  Using databases: %s, %s' % (DB_NAMES[db1], DB_NAMES[db2]))
        print()
        return (db1, db2)

    options = [(dbid, DB_NAMES[dbid]) for dbid in DB_ORDER]

    print('--- Step 1: Select the first contact store ---')
    print()
    db1 = _prompt_choice('Select store', options)
    print()
    print('  Selected: %s' % DB_NAMES[db1])
    print()

    print('--- Step 2: Select the second contact store ---')
    print()
    db2 = _prompt_choice('Select store', options)
    print()
    print('  Selected: %s' % DB_NAMES[db2])
    print()

    return (db1, db2)

##
## Generic folder selection
##

def _select_folder (db, label, preselected_fid=None):
    """Pick a contacts folder from a logged-in PIMDB.

    db is a PIMDB instance that has been logged in.
    label is a human-readable description like 'first' or 'second'.
    preselected_fid, if not None, skips the prompt and uses that fid.

    Returns the selected folder ID string.
    """

    folders = db.get_contacts_folders()
    if not folders:
        logging.error('No contact folders found in %s', db.get_dbid())
        raise AsynkParserError('No contact folders found.')

    ## Build (fid, display_label) list
    options = []
    for f in folders:
        fid  = f.get_itemid()
        name = f.get_name() if hasattr(f, 'get_name') else str(fid)
        options.append((fid, '%s  (ID: %s)' % (name, fid)))

    ## If a fid was pre-selected (from --folder), use it directly
    if preselected_fid is not None:
        print('  Using pre-selected folder: %s' % preselected_fid)
        return preselected_fid

    ## If only one folder, auto-select with confirmation
    if len(options) == 1:
        fid, display = options[0]
        print('  Only one folder available: %s' % display)
        return fid

    ## Default to 'default' for BB, first folder otherwise
    default_fid = None
    for fid, _ in options:
        if fid == 'default':
            default_fid = 'default'
            break
    if default_fid is None:
        default_fid = options[0][0]

    print('  Available folders for the %s store:' % label)
    print()
    fid = _prompt_choice('Select folder', options, default=default_fid)
    print()
    return fid

##
## Profile naming
##

def _generate_profile_name (config, db1_id, db2_id):
    """Generate a default profile name like 'gcbb1'.

    Returns a name that does not conflict with existing profiles.
    """

    existing = config.get_profile_names()
    pname_re = config.get_profile_name_re()
    base = '%s%s' % (db1_id, db2_id)

    for n in range(1, 1000):
        candidate = '%s%d' % (base, n)
        if candidate not in existing:
            ## Verify it matches the profile name regex
            if re.search('^' + pname_re + '$', candidate):
                return candidate

    ## Fallback -- should never get here
    return base + '999'

def _prompt_profile_name (config, db1_id, db2_id, preselected=None):
    """Prompt for a profile name with a sensible default.

    If preselected is provided (from --name), uses it directly.
    """

    if preselected:
        print('  Using profile name: %s' % preselected)
        return preselected

    default = _generate_profile_name(config, db1_id, db2_id)
    pname_re = config.get_profile_name_re()

    while True:
        name = _prompt_input('Profile name', default=default)
        if not name:
            continue

        ## Check regex
        if not re.search('^' + pname_re + '$', name):
            print('  Invalid name. Must match: %s' % pname_re)
            continue

        ## Check collision
        if config.profile_exists(name):
            print('  Profile "%s" already exists. Choose another.' % name)
            continue

        return name

##
## Sync settings
##

def _prompt_sync_settings (args, db1_id, db2_id):
    """Prompt for sync direction and conflict resolution.

    Returns (sync_dir, conflict_resolve) tuple.
    sync_dir is 'SYNC2WAY' or 'SYNC1WAY'.
    conflict_resolve is '1' or '2'.
    """

    ## Direction
    if hasattr(args, 'direction') and args.direction:
        sync_dir = 'SYNC1WAY' if args.direction == '1way' else 'SYNC2WAY'
        print('  Sync direction: %s' % sync_dir)
    else:
        options = [
            ('SYNC2WAY', 'Two-way sync (changes flow both directions)'),
            ('SYNC1WAY', 'One-way sync (first store -> second store)'),
        ]
        print()
        print('--- Sync direction ---')
        print()
        sync_dir = _prompt_choice('Direction', options, default='SYNC2WAY')

    ## Conflict resolution
    cr = getattr(args, 'conflict_resolve', None)
    if cr:
        print('  Conflict resolution: %s' % cr)
    else:
        options = [
            ('1', '%s wins (first store)' % DB_NAMES[db1_id]),
            ('2', '%s wins (second store)' % DB_NAMES[db2_id]),
        ]
        print()
        print('--- Conflict resolution ---')
        print()
        cr = _prompt_choice('On conflict', options, default='1')

    return (sync_dir, cr)

##
## DB-specific setup functions
##

def _setup_bb (args, config, coll_index):
    """Set up a BBDB collection.

    coll_index is 0 or 1 (which of the two stores this is).
    Returns (collection, db) tuple where db is a logged-in PIMDB.
    """

    ## Determine the store path
    store_path = None
    if args.store and len(args.store) > coll_index:
        store_path = args.store[coll_index]
    else:
        store_path = _prompt_input('BBDB file path', default='~/.bbdb')

    store_path = os.path.expanduser(store_path)

    ## Resolve the path the same way the BBDB code does internally
    abs_path = utils.abs_pathname(config, store_path)

    ## If the file doesn't exist, offer to create it
    if not os.path.exists(abs_path):
        print()
        print('  File not found: %s' % abs_path)
        create = _prompt_yesno('  Create it?', default=True)
        if create:
            from pimdb_bb import BBPIMDB
            BBPIMDB.new_store(abs_path)
            print('  Created: %s' % abs_path)
        else:
            raise AsynkParserError('BBDB file does not exist: %s'
                                   % abs_path)

    ## Create collection and login
    coll = coll_id_class['bb'](config=config, stid=store_path, pname=None)
    coll.login()

    return (coll, coll.get_db())

def _setup_gc (args, config, coll_index):
    """Set up a Google Contacts collection.

    coll_index is 0 or 1 (which of the two stores this is).
    Returns (collection, db) tuple where db is a logged-in PIMDB.
    """

    from asynk_subcmds import _apply_auth_to_coll

    ## Determine the username (label for token file)
    username = None
    if args.gcuser and len(args.gcuser) > coll_index:
        username = args.gcuser[coll_index]
    else:
        username = _prompt_input('Google account label (e.g. your email)')
        if not username:
            raise AsynkParserError('Google username is required.')

    coll = coll_id_class['gc'](config=config, pname=None)
    coll.set_username(username)

    ## Client secrets: resolved automatically by GCCollection.login()
    ## via the Phase 1 default credentials
    if args.gcpwd and len(args.gcpwd) > coll_index:
        coll.set_pwd(args.gcpwd[coll_index])

    print()
    print('  Authenticating with Google...')
    print('  (A browser window may open for OAuth authorization.)')
    print()
    coll.login()

    return (coll, coll.get_db())

def _setup_ex (args, config, coll_index):
    """Set up an Exchange Online collection.

    coll_index is 0 or 1 (which of the two stores this is).
    Returns (collection, db) tuple where db is a logged-in PIMDB.
    """

    from asynk_subcmds import _apply_auth_to_coll

    ## Account label (optional, used for token cache naming)
    username = None
    if args.ex_user and len(args.ex_user) > coll_index:
        username = args.ex_user[coll_index]
    else:
        username = _prompt_input(
            'Exchange account label (optional, for token cache)',
            default=None)

    coll = coll_id_class['ex'](config=config, pname=None)
    if username:
        coll.set_username(username)

    ## Client ID: resolved automatically from config by EXPIMDB
    if args.ex_client_id and len(args.ex_client_id) > coll_index:
        coll.set_pwd(args.ex_client_id[coll_index])

    if hasattr(args, 'ex_token_cache') and args.ex_token_cache:
        if len(args.ex_token_cache) > coll_index:
            coll.set_token_cache(args.ex_token_cache[coll_index])

    print()
    print('  Authenticating with Microsoft...')
    print('  (You will be given a URL and code to enter in a browser.)')
    print()
    coll.login()

    return (coll, coll.get_db())

def _setup_cd (args, config, coll_index):
    """Set up a CardDAV collection.

    coll_index is 0 or 1 (which of the two stores this is).
    Returns (collection, db) tuple where db is a logged-in PIMDB.
    """

    import getpass as _getpass

    ## Server URL
    server_url = None
    if args.store and len(args.store) > coll_index:
        server_url = args.store[coll_index]
    else:
        server_url = _prompt_input('CardDAV server URL')
        if not server_url:
            raise AsynkParserError('CardDAV server URL is required.')

    ## Username
    username = None
    if args.cduser and len(args.cduser) > coll_index:
        username = args.cduser[coll_index]
    else:
        username = _prompt_input('CardDAV username')
        if not username:
            raise AsynkParserError('CardDAV username is required.')

    ## Password
    password = None
    if args.cdpwd and len(args.cdpwd) > coll_index:
        password = args.cdpwd[coll_index]
    else:
        try:
            password = _getpass.getpass('CardDAV password: ')
        except (EOFError, KeyboardInterrupt):
            print()
            raise SystemExit('Setup cancelled.')
        if not password:
            raise AsynkParserError('CardDAV password is required.')

    coll = coll_id_class['cd'](config=config, stid=server_url, pname=None)
    coll.set_username(username)
    coll.set_pwd(password)

    print()
    print('  Connecting to CardDAV server...')
    print()
    coll.login()

    return (coll, coll.get_db())

## Dispatch table: DB ID -> setup function
_SETUP_FUNCS = {
    'bb': _setup_bb,
    'gc': _setup_gc,
    'ex': _setup_ex,
    'cd': _setup_cd,
}

##
## Profile creation
##

def _create_profile (config, alogger, args, pname, db1_id, db2_id,
                     coll1, fid1, coll2, fid2, sync_dir, cr):
    """Create a sync profile using the Asynk engine."""

    coll1.set_fid(fid1)
    coll2.set_fid(fid2)

    asynk = Asynk(config, alogger)
    asynk.set_op('op_create_profile')
    asynk.set_name(pname)
    asynk.set_dry_run(False)
    asynk.set_sync_dir(sync_dir)
    asynk.set_conflict_resolve(cr)
    asynk.set_sync_all(False)
    asynk.set_label_re(None)
    asynk.set_item_id(None)

    asynk.add_coll(coll1)
    asynk.add_coll(coll2)

    asynk.dispatch()
    return pname

##
## Profile summary
##

def _print_summary (pname, db1_id, db2_id, fid1, fid2, sync_dir, cr):
    """Print a summary of the created profile."""

    dir_label = 'Two-way sync' if sync_dir == 'SYNC2WAY' else 'One-way sync'
    cr_label = '%s wins' % DB_NAMES.get(
        db1_id if cr == '1' else db2_id, 'store %s' % cr)

    print()
    print('=' * 60)
    print('  Profile \'%s\' created successfully!' % pname)
    print('=' * 60)
    print()
    print('  Store 1:    %s' % DB_NAMES[db1_id])
    print('  Folder 1:   %s' % fid1)
    print('  Store 2:    %s' % DB_NAMES[db2_id])
    print('  Folder 2:   %s' % fid2)
    print('  Direction:  %s' % dir_label)
    print('  Conflicts:  %s' % cr_label)
    print()
    print('  Next steps:')
    print('    Dry run:  venv/bin/python asynk.py sync --name %s --dry-run'
          % pname)
    print('    Sync:     venv/bin/python asynk.py sync --name %s' % pname)
    print('    Details:  venv/bin/python asynk.py profile show --name %s'
          % pname)
    print()

##
## Main entry point -- called from asynk_subcmds.py
##

def cmd_init (args, config, alogger):
    """Interactive setup wizard handler."""

    _print_banner()

    ## Step 1: Select databases
    db1_id, db2_id = _select_dbs(args)

    ## Step 2: Credential setup and login for each DB
    print('--- Step 3: Set up credentials and login ---')
    print()

    setup1 = _SETUP_FUNCS.get(db1_id)
    setup2 = _SETUP_FUNCS.get(db2_id)

    if not setup1:
        raise AsynkParserError('Unsupported database: %s' % db1_id)
    if not setup2:
        raise AsynkParserError('Unsupported database: %s' % db2_id)

    print('  [Store 1: %s]' % DB_NAMES[db1_id])
    coll1, db1 = setup1(args, config, 0)
    print()

    print('  [Store 2: %s]' % DB_NAMES[db2_id])
    coll2, db2 = setup2(args, config, 1)
    print()

    ## Step 3: Folder selection
    print('--- Step 4: Select folders ---')
    print()

    pre_fid1 = args.folder[0] if args.folder and len(args.folder) > 0 else None
    pre_fid2 = args.folder[1] if args.folder and len(args.folder) > 1 else None

    fid1 = _select_folder(db1, 'first (%s)' % DB_NAMES[db1_id],
                          preselected_fid=pre_fid1)
    fid2 = _select_folder(db2, 'second (%s)' % DB_NAMES[db2_id],
                          preselected_fid=pre_fid2)

    ## Step 4: Profile naming
    print('--- Step 5: Name your profile ---')
    print()
    pname = _prompt_profile_name(config, db1_id, db2_id,
                                 preselected=args.name)
    print()

    ## Step 5: Sync settings
    sync_dir, cr = _prompt_sync_settings(args, db1_id, db2_id)

    ## Step 6: Create the profile
    print()
    print('  Creating profile...')
    _create_profile(config, alogger, args, pname, db1_id, db2_id,
                    coll1, fid1, coll2, fid2, sync_dir, cr)

    ## Step 7: Summary
    _print_summary(pname, db1_id, db2_id, fid1, fid2, sync_dir, cr)
