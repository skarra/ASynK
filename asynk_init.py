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

import logging, os, sys

CUR_DIR        = os.path.abspath('')
ASYNK_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXTRA_PATHS = [os.path.join(ASYNK_BASE_DIR, 'lib'),
               os.path.join(ASYNK_BASE_DIR, 'asynk'),]
sys.path = EXTRA_PATHS + sys.path

import utils
from   state            import Config
from   state_collection import collection_id_to_class as coll_id_class

## DB IDs and their human-friendly names.  Outlook is excluded — it is
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
    print('  ASynK %s — Interactive Setup Wizard' % utils.asynk_ver)
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

def _select_dbs ():
    """Present the DB menu twice and return (db1_id, db2_id)."""

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
## Main entry point — called from asynk_subcmds.py
##

def cmd_init (args, config, alogger):
    """Interactive setup wizard handler."""

    _print_banner()
    db1, db2 = _select_dbs()

    print('--- Step 3: Set up credentials ---')
    print()
    print('  Setting up %s <-> %s sync ...' % (DB_NAMES[db1], DB_NAMES[db2]))
    print()
    print('  (Credential setup and folder selection not yet implemented.)')
    print('  (This will be completed in subsequent sub-phases.)')
    print()
