# Taken from the anaconda and python-meh sources
#
# Copyright (C) 2009-2020  Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Martin Sivak <msivak@redhat.com>
# Author: Martin Kolman <mkolman@redhat.com>

include ./branch-config.mk

PKGNAME=initial-setup
VERSION=$(shell awk '/Version:/ { print $$2 }' $(PKGNAME).spec)
RELEASE=$(shell awk '/Release:/ { print $$2 }' $(PKGNAME).spec | sed -e 's|%.*$$||g')
TAG=r$(VERSION)-$(RELEASE)

PYTHON=python3
# Arguments used for setup.py call for creating archive
BUILD_ARGS ?= sdist bdist_wheel

# LOCALIZATION SETTINGS
L10N_REPOSITORY ?= https://github.com/rhinstaller/initial-setup-l10n.git
L10N_REPOSITORY_RW ?= git@github.com:rhinstaller/initial-setup-l10n.git
# Branch used in localization repository. This should be master all the time.
GIT_L10N_BRANCH ?= master

# Name of our local TMT run
TMT_ID ?= initial-setup-tests
TMT_COPR_ANACONDA_REPO ?=

default: all

all: po-files

.PHONY: install
install:
	$(PYTHON) setup.py install --root=$(DESTDIR)
	$(MAKE) -C po install

.PHONY: clean
clean:
	-rm *.tar.gz ChangeLog initial-setup-*.src.rpm
	-rm -rf $(TEST_BUILD_DIR) dist/ initial_setup.egg-info
	-find . -name "*.pyc" -exec rm -rf {} \;

# local run of TMT tests
# local run will be executed on source instead of RPM. It's much faster and easier, however,
# Packit and Gating will execute the tests on an installed RPM; see test fmf specification.
.PHONY: test
test:
# Command will execute all steps first time (see TMT plans to find out more). On repeated run only
# discover and execute steps will be executed. This will save a lot of time during test development.
# To run the skipped prepare steps again please call `make test-cleanup`.
	if [ -z "$(TMT_COPR_ANACONDA_REPO)" ]; then \
		tmt run -vvv --id $(TMT_ID) --until report discover -f execute -f; \
	else \
		tmt run -vvv --id $(TMT_ID) --until report prepare -h install --copr "$(TMT_COPR_ANACONDA_REPO)" --package anaconda discover -f execute -f; \
	fi

# clean the container and test data
.PHONY: test-cleanup
test-cleanup:
	tmt run -vvv --rm --id $(TMT_ID) --after report finish -f

.PHONY: ChangeLog
ChangeLog:
	(GIT_DIR=.git git log > .changelog.tmp && mv .changelog.tmp ChangeLog; rm -f .changelog.tmp) || (touch ChangeLog; echo 'git directory not found: installing possibly empty changelog.' >&2)

.PHONY: tag
tag:
	git tag -a -m "Tag as $(TAG)" -f $(TAG)
	@echo "Tagged as $(TAG)"

.PHONY: release
release:
	$(MAKE) bumpver
	$(MAKE) commit
	$(MAKE) tag
	$(MAKE) archive

.PHONY: archive
archive: po-pull ChangeLog
	$(PYTHON) setup.py $(BUILD_ARGS)
	@echo "The archive is in $(PKGNAME)-$(VERSION).tar.gz"

.PHONY: local
local: po-pull ChangeLog
	@rm -rf $(PKGNAME)-$(VERSION).tar.gz
	@rm -rf /tmp/$(PKGNAME)-$(VERSION) /tmp/$(PKGNAME)
	@dir=$$PWD; cp -a $$dir /tmp/$(PKGNAME)-$(VERSION)
	@cd /tmp/$(PKGNAME)-$(VERSION) ; $(PYTHON) setup.py -q sdist
	@cp /tmp/$(PKGNAME)-$(VERSION)/dist/$(PKGNAME)-$(VERSION).tar.gz .
	@rm -rf /tmp/$(PKGNAME)-$(VERSION)
	@echo "The archive is in $(PKGNAME)-$(VERSION).tar.gz"

.PHONY: rpmlog
rpmlog:
	@git log --no-merges --pretty="format:- %s (%ae)" $(TAG).. |sed -e 's/@.*)/)/'
	@echo

.PHONY: po-files
po-files:
	$(MAKE) -C po

.PHONY: potfile
potfile:
	$(MAKE) -C po potfile

.PHONY: po-pull
po-pull:
	TEMP_DIR=$$(mktemp --tmpdir -d $(PKGNAME)-localization-XXXXXXXXXX) && \
	git clone --depth 1 -b $(GIT_L10N_BRANCH) -- $(L10N_REPOSITORY) $$TEMP_DIR && \
	cp $$TEMP_DIR/$(L10N_DIR)/*.po ./po/ && \
	rm -rf $$TEMP_DIR

.PHONY: potfile
po-push: potfile
# This algorithm will make these steps:
# - clone localization repository
# - copy pot file to this repository
# - check if pot file is changed (ignore the POT-Creation-Date otherwise it's always changed)
# - if not changed:
#   - remove cloned repository
# - if changed:
#   - add pot file
#   - commit pot file
#   - tell user to verify this file and push to the remote from the temp dir
	TEMP_DIR=$$(mktemp --tmpdir -d $(PKGNAME)-localization-XXXXXXXXXX) || exit 1 ; \
	git clone --depth 1 -b $(GIT_L10N_BRANCH) -- $(L10N_REPOSITORY_RW) $$TEMP_DIR || exit 2 ; \
	cp ./po/$(PKGNAME).pot $$TEMP_DIR/$(L10N_DIR)/ || exit 3 ; \
	pushd $$TEMP_DIR/$(L10N_DIR) ; \
	git difftool --trust-exit-code -y -x "diff -u -I '^\"POT-Creation-Date: .*$$'" HEAD ./$(PKGNAME).pot &>/dev/null ; \
	if [ $$? -eq 0  ] ; then \
		popd ; \
		echo "Pot file is up to date" ; \
		rm -rf $$TEMP_DIR ; \
	else \
		git add ./$(PKGNAME).pot && \
		git commit -m "Update $(PKGNAME).pot" && \
		popd && \
		echo "Pot file updated for the localization repository $(L10N_REPOSITORY)" && \
		echo "Please confirm changes and push:" && \
		echo "$$TEMP_DIR" ; \
	fi ;

.PHONY: po-push
bumpver: po-push
	read -p "Please see the above message. Verify and push localization commit. Press anything to continue." -n 1 -r

	@NEWSUBVER=$$((`echo $(VERSION) |cut -d . -f 3` + 1)) ; \
	NEWVERSION=`echo $(VERSION).$$NEWSUBVER |cut -d . -f 1,2,4` ; \
	DATELINE="* `LANG=c date "+%a %b %d %Y"` `git config user.name` <`git config user.email`> - $$NEWVERSION-1"  ; \
	cl=`grep -n %changelog initial-setup.spec |cut -d : -f 1` ; \
	tail --lines=+$$(($$cl + 1)) initial-setup.spec > speclog ; \
	(head -n $$cl initial-setup.spec ; echo "$$DATELINE" ; make --quiet --no-print-directory rpmlog 2>/dev/null ; echo ""; cat speclog) > initial-setup.spec.new ; \
	mv initial-setup.spec.new initial-setup.spec ; rm -f speclog ; \
	sed -i "s/Version: $(VERSION)/Version: $$NEWVERSION/" initial-setup.spec ; \
	sed -i "s/version = \"$(VERSION)\"/version = \"$$NEWVERSION\"/" setup.py ; \
	sed -i "s/__version__ = \"$(VERSION)\"/__version__ = \"$$NEWVERSION\"/" initial_setup/__init__.py ; \

.PHONY: commit
commit:
	git add initial-setup.spec initial_setup/__init__.py po/initial-setup.pot setup.py ; \
	git commit -m "New version $(VERSION)" ; \
