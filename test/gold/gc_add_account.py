##
## Created : Sat May 17 15:47:00 PDT 2026
##
## Copyright (C) 2026 Sriram Karra <karra.etc@gmail.com>
##
## This file is part of ASynK
##
## ASynK is free software: you can redistribute it and/or modify it under
## the terms of the GNU Affero GPL (GNU AGPL) as published by the
## Free Software Foundation, version 3 of the License
##
## ASynK is distributed in the hope that it will be useful, but WITHOUT
## ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
## FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
## License for more details.
##
## You should have a copy of the license in the doc/ directory of ASynK.  If
## not, see <http://www.gnu.org/licenses/>.
##
## ####
##
## Run a single OAuth2 dance for a Google account and save the token.
## No tests are executed.  This is meant to be used to build a pool of
## test account credentials for spreading API quota load.
##
## Usage:
##   python gc_add_account.py --cs /path/to/credentials.json --user acct2
##
## Or via Makefile:
##   make gc-add-account GOOGLE_CL_SECRET=~/creds.json GC_USER=acct2
##

import getopt, logging, os, os.path, pickle, shutil, sys

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

## The People API scope — must match what pimdb_gc.py uses.
SCOPES = ['https://www.googleapis.com/auth/contacts']

## Persistent credentials directory (same as test_gc.py / test_sync_gc_bb.py)
GC_CREDS_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'gc_creds'))

def run_oauth_dance (cs_file, user_label):
    """Run the OAuth2 flow for the given user label, save the token,
    and validate that it works by listing contact groups.

    cs_file:    absolute path to the OAuth2 client secrets JSON
    user_label: label for the token file (e.g. 'test', 'acct2')
    """

    if not os.path.exists(GC_CREDS_DIR):
        os.makedirs(GC_CREDS_DIR)

    ## Copy client secrets into gc_creds/ if not already there
    cs_dest = os.path.join(GC_CREDS_DIR, os.path.basename(cs_file))
    if not os.path.exists(cs_dest):
        shutil.copyfile(cs_file, cs_dest)

    token_file = os.path.join(GC_CREDS_DIR, '%s.token.pickle' % user_label)

    creds = None

    ## Load existing token if present
    if os.path.exists(token_file):
        with open(token_file, 'rb') as f:
            creds = pickle.load(f)

    ## If no valid credentials, run the OAuth dance
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print('Refreshing expired token for "%s"...' % user_label)
            creds.refresh(Request())
        else:
            print('Starting OAuth2 flow for "%s"...' % user_label)
            print('A browser window will open for Google consent.')
            flow = InstalledAppFlow.from_client_secrets_file(cs_dest, SCOPES)
            creds = flow.run_local_server(port=0)

        ## Save the token
        with open(token_file, 'wb') as f:
            pickle.dump(creds, f)
        print('Token saved: %s' % token_file)
    else:
        print('Token for "%s" is still valid: %s' % (user_label, token_file))

    ## Validate: make a lightweight API call
    print('Validating credentials...')
    try:
        service = build('people', 'v1', credentials=creds)
        result = service.contactGroups().list(pageSize=5).execute()
        groups = result.get('contactGroups', [])
        print('  OK — account has %d contact group(s).' % len(groups))
        ## Show the account email if available from the 'people/me' resource
        try:
            me = service.people().get(
                resourceName='people/me',
                personFields='emailAddresses'
            ).execute()
            emails = me.get('emailAddresses', [])
            if emails:
                print('  Account email: %s' % emails[0].get('value', '?'))
        except Exception:
            pass  # not critical — some scopes may not allow this
    except Exception as e:
        print('  WARNING: Validation failed: %s' % e)
        print('  The token was saved but may not be usable.')
        sys.exit(1)

    print('\nDone.  Account "%s" is ready for testing.' % user_label)

def main ():
    cs_file = None
    user_label = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], '', ['cs=', 'user='])
    except getopt.error as msg:
        print('Usage: python gc_add_account.py '
              '--cs /path/to/credentials.json --user <label>')
        sys.exit(2)

    for option, arg in opts:
        if option == '--cs':
            cs_file = os.path.abspath(arg)
        elif option == '--user':
            user_label = arg

    if not cs_file:
        print('ERROR: --cs /path/to/credentials.json is required.')
        sys.exit(1)

    if not user_label:
        print('ERROR: --user <label> is required (e.g. test, acct2, acct3).')
        sys.exit(1)

    if not os.path.exists(cs_file):
        print('ERROR: Client secrets file not found: %s' % cs_file)
        sys.exit(1)

    run_oauth_dance(cs_file, user_label)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.WARNING)
    main()
