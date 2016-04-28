# Taken from the anaconda and python-meh sources
#
# Copyright (C) 2009-2016  Red Hat, Inc.
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
# Authors: Martin Sivak <msivak@redhat.com>
#          Martin Kolman <mkolman@redhat.com>

PKGNAME=initial-setup
VERSION=$(shell awk '/Version:/ { print $$2 }' $(PKGNAME).spec)
RELEASE=$(shell awk '/Release:/ { print $$2 }' $(PKGNAME).spec | sed -e 's|%.*$$||g')
TAG=r$(VERSION)-$(RELEASE)

PREFIX=/usr

PYTHON=python2

ZANATA_PULL_ARGS = --transdir po/
ZANATA_PUSH_ARGS = --srcdir po/ --push-type source --force

default: all

all: po-files

install:
	$(PYTHON) setup.py install --root=$(DESTDIR)
	$(MAKE) -C po install

clean:
	-rm *.tar.gz ChangeLog
	-find . -name "*.pyc" -exec rm -rf {} \;

test:
	echo 'tests not yet implemented'

ChangeLog:
	(GIT_DIR=.git git log > .changelog.tmp && mv .changelog.tmp ChangeLog; rm -f .changelog.tmp) || (touch ChangeLog; echo 'git directory not found: installing possibly empty changelog.' >&2)

tag:
	git tag -a -m "Tag as $(TAG)" -f $(TAG)
	@echo "Tagged as $(TAG)"

release: tag archive

archive: po-pull
	@rm -f ChangeLog
	@make ChangeLog
	git archive --format=tar --prefix=$(PKGNAME)-$(VERSION)/ $(TAG) > $(PKGNAME)-$(VERSION).tar
	mkdir $(PKGNAME)-$(VERSION)
	cp -r po $(PKGNAME)-$(VERSION)
	cp ChangeLog $(PKGNAME)-$(VERSION)/
	tar -rf $(PKGNAME)-$(VERSION).tar $(PKGNAME)-$(VERSION)
	gzip -9 $(PKGNAME)-$(VERSION).tar
	rm -rf $(PKGNAME)-$(VERSION)
	git checkout -- po/$(PKGNAME).pot
	@echo "The archive is in $(PKGNAME)-$(VERSION).tar.gz"

local: po-pull
	@rm -f ChangeLog
	@make ChangeLog
	@rm -rf $(PKGNAME)-$(VERSION).tar.gz
	@rm -rf /tmp/$(PKGNAME)-$(VERSION) /tmp/$(PKGNAME)
	@dir=$$PWD; cp -a $$dir /tmp/$(PKGNAME)-$(VERSION)
	@cd /tmp/$(PKGNAME)-$(VERSION) ; $(PYTHON) setup.py -q sdist
	@cp /tmp/$(PKGNAME)-$(VERSION)/dist/$(PKGNAME)-$(VERSION).tar.gz .
	@rm -rf /tmp/$(PKGNAME)-$(VERSION)
	@echo "The archive is in $(PKGNAME)-$(VERSION).tar.gz"

rpmlog:
	@git log --pretty="format:- %s (%ae)" $(TAG).. |sed -e 's/@.*)/)/'
	@echo

po-files:
	$(MAKE) -C po

potfile:
	$(MAKE) -C po potfile

po-pull:
	rpm -q zanata-python-client &>/dev/null || ( echo "need to run: yum install zanata-python-client"; exit 1 )
	zanata pull $(ZANATA_PULL_ARGS)

bumpver: potfile
	zanata push $(ZANATA_PUSH_ARGS) || ( echo "zanata push failed"; exit 1 )
	@NEWSUBVER=$$((`echo $(VERSION) |cut -d . -f 4` + 1)) ; \
	NEWVERSION=`echo $(VERSION).$$NEWSUBVER |cut -d . -f 1,2,3,5` ; \
	DATELINE="* `LANG=c date "+%a %b %d %Y"` `git config user.name` <`git config user.email`> - $$NEWVERSION-1"  ; \
	cl=`grep -n %changelog initial-setup.spec |cut -d : -f 1` ; \
	tail --lines=+$$(($$cl + 1)) initial-setup.spec > speclog ; \
	(head -n $$cl initial-setup.spec ; echo "$$DATELINE" ; make --quiet rpmlog 2>/dev/null ; echo ""; cat speclog) > initial-setup.spec.new ; \
	mv initial-setup.spec.new initial-setup.spec ; rm -f speclog ; \
	sed -i "s/Version: $(VERSION)/Version: $$NEWVERSION/" initial-setup.spec ; \
	sed -i "s/version = \"$(VERSION)\"/version = \"$$NEWVERSION\"/" setup.py ; \
	sed -i "s/__version__ = \"$(VERSION)\"/__version__ = \"$$NEWVERSION\"/" initial_setup/__init__.py ; \

install-po-files:
	$(MAKE) -C po install


.PHONY: clean install tag archive local
