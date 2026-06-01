##
## Created : Sun Jun 01 16:03:00 PDT 2026
## SPDX-FileCopyrightText: 2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
##
## Thin wrapper around the 'keyring' library for storing and retrieving
## iCloud app-specific passwords from the OS-native credential store
## (macOS Keychain, GNOME Keyring, Windows Credential Locker).
##
## All functions degrade gracefully when keyring is not installed or the
## backend is unavailable.
##

import logging

KEYCHAIN_SERVICE = 'asynk-icloud'

def get_password (username):
    """Retrieve the stored iCloud app-specific password for the given
    Apple ID.  Returns None if not found or if keyring is unavailable."""

    try:
        import keyring as _kr
        pwd = _kr.get_password(KEYCHAIN_SERVICE, username)
        if pwd:
            logging.debug('Retrieved iCloud password from OS keychain '
                          'for %s', username)
        return pwd
    except Exception as e:
        logging.debug('Could not read from OS keychain: %s', e)
        return None

def set_password (username, password):
    """Store the iCloud app-specific password in the OS keychain.
    Silently fails if keyring is unavailable."""

    try:
        import keyring as _kr
        _kr.set_password(KEYCHAIN_SERVICE, username, password)
        logging.debug('Saved iCloud password to OS keychain for %s',
                      username)
        return True
    except Exception as e:
        logging.warning('Could not save to OS keychain: %s', e)
        return False

def delete_password (username):
    """Remove the stored iCloud password from the OS keychain.
    Silently fails if keyring is unavailable or entry not found."""

    try:
        import keyring as _kr
        _kr.delete_password(KEYCHAIN_SERVICE, username)
        logging.debug('Deleted iCloud password from OS keychain for %s',
                      username)
        return True
    except Exception as e:
        logging.debug('Could not delete from OS keychain: %s', e)
        return False
