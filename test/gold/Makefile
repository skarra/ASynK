##
## Created : Sat Aug 10 06:17:20 IST 2013
##
## Copyright (C) 2013 Sriram Karra <karra.etc@gmail.com>
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

## Use this Makefile to drive the automated regression testing of ASynK.

PYTHON ?= ../../venv/bin/python3

all: state cmdline bb

clean:
	rm -rf user_dir *~ *.bak temp.bbdb

## distclean also removes gc_creds/ which holds cached OAuth2 tokens
## and client secrets.  Use this to force re-authentication.
distclean: clean
	rm -rf gc_creds

state:
	$(PYTHON) test_state.py

cmdline:
	$(PYTHON) test_cmdline.py

bb:
	$(PYTHON) test_bb_read.py
	$(PYTHON) test_bb_write.py

## Google Contacts tests — NOT included in 'all' because they need live
## credentials and network access.  Run with:
##   make gc GOOGLE_CL_SECRET=~/path/to/credentials.json
## Optionally override the user label:
##   make gc GOOGLE_CL_SECRET=~/creds.json GC_USER=myemail
GOOGLE_CL_SECRET ?=
GC_USER ?= test

gc:
ifndef GOOGLE_CL_SECRET
	@echo "ERROR: GOOGLE_CL_SECRET not set."
	@echo "Usage: make gc GOOGLE_CL_SECRET=~/path/to/credentials.json"
	@exit 1
endif
	$(PYTHON) test_gc.py --cs $(GOOGLE_CL_SECRET) --user $(GC_USER)
