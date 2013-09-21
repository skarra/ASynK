#!/usr/bin/python
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

all: state bb

clean:
	rm -rf user_dir *~ *.bak

state:
	python test_state.py

bb:
	python test_bb_read.py
	python test_bb_write.py
