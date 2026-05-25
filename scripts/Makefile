##
## Created : Thu May 17 13:02:14 IST 2012
## SPDX-FileCopyrightText: 2012-2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK

##
## You do not need to use this Makefile to run the program. If all you
## want to do is to use ASynK, there is nothing here. Please move on
## and take a look at the documentation.
##
## This Makefile automates some of the steps in the release
## process. Ideally we want to automate all of the following setps
## based on a version string, which is also used to tag the source repo
##
##  1. Change the version string in asynk.py, which is used in --version output
##
##  2. Commit the above change
##
##  3. Tag the source with the version number
##
##  4. Clone the current repo into a temporary repository
##
##  5. cd to the repository and build the documentation
##
##  6. Edit the announcements in gae/index.html, and update the
##     timestamp for the page in the footer.
##
##  7. Push the updates to gae
##
##  8. Change the version with a '+' added to the version string.
##
##  9. Commit the changes
##
## 10. Push changes to upstream git repo
##
## The steps that involve pushing things to github and gae will come
## under the 'install' target. The rest will come under the default
## target. There is nothing to clean up at this stage.
##

src = ../asynk/utils.py

default:
ifeq ($(strip ${REL}),)
	$(error "Have to specify a release. Usage: 'make REL=<rel>'")
endif
	@echo
	@echo ==== Replacing version identifier in ${src}...
	sed -i .bak "s/^asynk_ver = \'.*\'/asynk_ver = \'${REL}\'/" ${src}

	@echo ==== Comitting change to repository...
	git add ${src}
	cd .. && git commit -m 'Bumping up version to ${REL} for release'

	@echo
	@echo ==== Tagging release with ${REL}...
	cd .. && git tag -a -m 'Release ${REL}' ${REL}

install:
	@echo
	@echo ==== Pushing release changes with tags upstream...
	cd .. && git push --follow-tags

	@echo
	@echo ==== Replacing version identifier in ${src} to dev ver...
	sed -i .bak "s/^asynk_ver = \'.*\'/asynk_ver = \'${REL}+\'/" ${src}

	@echo ==== Comitting change to repository...
	git add ${src}
	cd .. && git commit -m 'Bumping up version to ${REL}+ for development'
