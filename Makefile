# Taken from the anaconda sources
#
# Copyright (C) 2009-2013  Red Hat, Inc.
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

ANACONDA_PATH=${HOME}/Work/anaconda/msivak
PYKICKSTART_PATH=${HOME}/Work/pykickstart/master

ZANATA_PULL_ARGS = --transdir po/

default: all

all: po-files

po-files:
	$(MAKE) -C po

# GUI TESTING
rungui:
	ANACONDA_DATA=${ANACONDA_PATH}/data \
	ANACONDA_WIDGETS_OVERRIDES=${ANACONDA_PATH}/widgets/python \
	ANACONDA_WIDGETS_DATA=${ANACONDA_PATH}/widgets/data \
	ANACONDA_INSTALL_CLASSES=${ANACONDA_PATH}/pyanaconda/installclasses \
	PYTHONPATH=.:${ANACONDA_PATH}/pyanaconda/isys/.libs:${ANACONDA_PATH}/widgets/python/:${ANACONDA_PATH}/widgets/src/.libs/:${ANACONDA_PATH}:${PYKICKSTART_PATH} \
	LD_LIBRARY_PATH=${ANACONDA_PATH}/widgets/src/.libs \
	UIPATH=gui/:${ANACONDA_PATH}/pyanaconda/ui/gui/ \
	GI_TYPELIB_PATH=${ANACONDA_PATH}/widgets/src/ \
	GLADE_CATALOG_SEARCH_PATH=${ANACONDA_PATH}/widgets/glade \
	GLADE_MODULE_SEARCH_PATH=${ANACONDA_PATH}/widgets/src/.libs \
	./initial-setup

runtui:
	ANACONDA_DATA=${ANACONDA_PATH}/data \
	ANACONDA_INSTALL_CLASSES=${ANACONDA_PATH}/pyanaconda/installclasses \
	PYTHONPATH=.:${ANACONDA_PATH}:${ANACONDA_PATH}/pyanaconda/isys/.libs:${PYKICKSTART_PATH}  \
	DISPLAY= ./initial-setup

runglade:
	ANACONDA_DATA=${ANACONDA_PATH}/data \
	ANACONDA_WIDGETS_OVERRIDES=${ANACONDA_PATH}/widgets/python \
	ANACONDA_WIDGETS_DATA=${ANACONDA_PATH}/widgets/data \
	ANACONDA_INSTALL_CLASSES=${ANACONDA_PATH}/pyanaconda/installclasses \
	PYTHONPATH=.:${ANACONDA_PATH}:${ANACONDA_PATH}/pyanaconda/isys/.libs:${ANACONDA_PATH}/widgets/python/:${ANACONDA_PATH}/widgets/src/.libs/ \
	LD_LIBRARY_PATH=${ANACONDA_PATH}/widgets/src/.libs \
	UIPATH=${ANACONDA_PATH}/pyanaconda/ui/gui/ \
	GI_TYPELIB_PATH=${ANACONDA_PATH}/widgets/src/ \
	GLADE_CATALOG_SEARCH_PATH=${ANACONDA_PATH}/widgets/glade \
	GLADE_MODULE_SEARCH_PATH=${ANACONDA_PATH}/widgets/src/.libs \
	glade ${GLADE_FILE}

runpy:
	ANACONDA_DATA=${ANACONDA_PATH}/data \
	ANACONDA_WIDGETS_OVERRIDES=${ANACONDA_PATH}/widgets/python \
	ANACONDA_WIDGETS_DATA=${ANACONDA_PATH}/widgets/data \
	ANACONDA_INSTALL_CLASSES=${ANACONDA_PATH}/pyanaconda/installclasses \
	PYTHONPATH=.:${ANACONDA_PATH}:${ANACONDA_PATH}/pyanaconda/isys/.libs:${ANACONDA_PATH}/widgets/python/:${ANACONDA_PATH}/widgets/src/.libs/ \
	LD_LIBRARY_PATH=${ANACONDA_PATH}/widgets/src/.libs \
	UIPATH=gui/:${ANACONDA_PATH}/pyanaconda/ui/gui/ \
	GI_TYPELIB_PATH=${ANACONDA_PATH}/widgets/src/ \
	GLADE_CATALOG_SEARCH_PATH=${ANACONDA_PATH}/widgets/glade \
	GLADE_MODULE_SEARCH_PATH=${ANACONDA_PATH}/widgets/src/.libs \
	ipython

potfile:
	$(MAKE) -C po potfile

po-pull:
	rpm -q zanata-python-client &>/dev/null || ( echo "need to run: dnf install zanata-python-client"; exit 1 )
	zanata pull $(ZANATA_PULL_ARGS)

install-po-files:
	$(MAKE) -C po install
