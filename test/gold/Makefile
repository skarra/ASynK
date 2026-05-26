##
## Created : Sat Aug 10 06:17:20 IST 2013
## SPDX-FileCopyrightText: 2013-2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK

## Use this Makefile to drive the automated regression testing of ASynK.

PYTHON ?= ../../venv/bin/python3

all: state cmdline bb sync-bb-bb ex ex-live-best-effort gc-best-effort sync-gc-bb-best-effort sync-gc-gc-best-effort cd-best-effort

clean:
	rm -rf user_dir user_dir_gc_gc *~ *.bak temp.bbdb test_sync_*.bbdb

## distclean also removes gc_creds/ and ex_creds/ which hold cached OAuth2
## tokens.  Use this to force re-authentication.
distclean: clean
	rm -rf gc_creds ex_creds

## Add a Google test account credential.  Each invocation runs one OAuth
## dance and saves the token — no tests are executed.
##   make gc-add-account GOOGLE_CL_SECRET=~/creds.json GC_USER=acct2
gc-add-account:
ifndef GOOGLE_CL_SECRET
	$(error GOOGLE_CL_SECRET is required.  Usage: make gc-add-account GOOGLE_CL_SECRET=~/creds.json GC_USER=acct2)
endif
ifndef GC_USER
	$(error GC_USER is required (e.g. test, acct2).  Usage: make gc-add-account GOOGLE_CL_SECRET=~/creds.json GC_USER=acct2)
endif
	$(PYTHON) gc_add_account.py --cs $(GOOGLE_CL_SECRET) --user $(GC_USER)

## List all cached Google test account tokens.
gc-list-accounts:
	@echo "Cached Google test accounts in gc_creds/:"
	@ls -1 gc_creds/*.token.pickle 2>/dev/null | sed 's|.*/||;s|\.token\.pickle||' || echo "  (none)"

state:
	$(PYTHON) test_state.py

cmdline:
	$(PYTHON) test_cmdline.py

bb:
	$(PYTHON) test_bb_read.py
	$(PYTHON) test_bb_write.py

## BB<->BB sync engine tests (offline, always runs)
sync-bb-bb:
	$(PYTHON) test_sync_bb_bb.py

## Exchange / Graph API unit tests (offline, mocked HTTP — always runs)
ex:
	$(PYTHON) -m unittest test_msgraph_client -v
	$(PYTHON) -m unittest test_contact_field_preservation_ex -v

## Exchange Online live integration tests (requires real credentials).
##   First run:  make ex-live EX_CLIENT_ID=YOUR-AZURE-AD-CLIENT-ID
##   After that: make ex-live  (reuses cached credentials in ex_creds/)
## 'make all' uses ex-live-best-effort which gracefully skips if no
## credentials are available.  'make ex-live' requires credentials and
## fails if missing.
EX_TENANT_ID ?= common

ex-live:
ifdef EX_CLIENT_ID
	$(PYTHON) test_ex_live.py --client-id $(EX_CLIENT_ID) --tenant-id $(EX_TENANT_ID)
else
	$(PYTHON) test_ex_live.py --tenant-id $(EX_TENANT_ID)
endif

ex-live-best-effort:
ifdef EX_CLIENT_ID
	$(PYTHON) test_ex_live.py --client-id $(EX_CLIENT_ID) --tenant-id $(EX_TENANT_ID)
else
	$(PYTHON) test_ex_live.py --tenant-id $(EX_TENANT_ID) --best-effort
endif

## Google Contacts integration tests.
##   First run:  make gc GOOGLE_CL_SECRET=~/path/to/credentials.json
##   After that: make gc  (reuses cached credentials in gc_creds/)
## 'make all' uses gc-best-effort which gracefully skips if no credentials
## are available.  'make gc' requires credentials and fails if missing.
GC_USER ?= test

gc:
ifdef GOOGLE_CL_SECRET
	$(PYTHON) test_gc.py --cs $(GOOGLE_CL_SECRET) --user $(GC_USER)
else
	$(PYTHON) test_gc.py --user $(GC_USER)
endif

gc-best-effort:
ifdef GOOGLE_CL_SECRET
	$(PYTHON) test_gc.py --cs $(GOOGLE_CL_SECRET) --user $(GC_USER)
else
	$(PYTHON) test_gc.py --user $(GC_USER) --best-effort
endif

## GC<->BB sync engine tests.
## Same best-effort pattern as gc above.
sync-gc-bb:
ifdef GOOGLE_CL_SECRET
	$(PYTHON) test_sync_gc_bb.py --cs $(GOOGLE_CL_SECRET) --user $(GC_USER)
else
	$(PYTHON) test_sync_gc_bb.py --user $(GC_USER)
endif

sync-gc-bb-best-effort:
ifdef GOOGLE_CL_SECRET
	$(PYTHON) test_sync_gc_bb.py --cs $(GOOGLE_CL_SECRET) --user $(GC_USER)
else
	$(PYTHON) test_sync_gc_bb.py --user $(GC_USER) --best-effort
endif

## GC<->GC sync engine tests.
## Same best-effort pattern as gc above.
sync-gc-gc:
ifdef GOOGLE_CL_SECRET
	$(PYTHON) test_sync_gc_gc.py --cs $(GOOGLE_CL_SECRET) --user $(GC_USER)
else
	$(PYTHON) test_sync_gc_gc.py --user $(GC_USER)
endif

sync-gc-gc-best-effort:
ifdef GOOGLE_CL_SECRET
	$(PYTHON) test_sync_gc_gc.py --cs $(GOOGLE_CL_SECRET) --user $(GC_USER)
else
	$(PYTHON) test_sync_gc_gc.py --user $(GC_USER) --best-effort
endif

## CardDAV integration tests.
CD_URL ?= http://127.0.0.1:5232/
CD_USER ?= admin
CD_PASS ?= admin

cd:
	$(PYTHON) test_cd_integration.py --url $(CD_URL) --user $(CD_USER) --pass $(CD_PASS)

cd-best-effort:
	$(PYTHON) test_cd_integration.py --url $(CD_URL) --user $(CD_USER) --pass $(CD_PASS) --best-effort

## CD↔BB sync engine tests.
## Same best-effort pattern as gc above.
sync-cd-bb:
	$(PYTHON) test_sync_cd_bb.py --url $(CD_URL) --user $(CD_USER) --pass $(CD_PASS)

sync-cd-bb-best-effort:
	$(PYTHON) test_sync_cd_bb.py --url $(CD_URL) --user $(CD_USER) --pass $(CD_PASS) --best-effort

