#!/usr/bin/python
# Setup file for Python DI
#
# Copyright (C) 2012  Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
# Red Hat Author(s): Martin Sivak <msivak@redhat.com>
#

import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

from glob import *
import os

data_files = [('/lib/systemd/system', glob('systemd/*.service'))]

# add the firstboot start script for s390 architectures
if os.uname()[4].startswith('s390'):
    data_files.append(('/etc/profile.d', ['scripts/inital-setup.sh']))
    data_files.append(('/etc/profile.d', ['scripts/inital-setup.csh']))

setup(
    name = "inital-setup",
    version = "0.1",
    author = "Martin Sivak",
    author_email = "msivak@redhat.com",
    description='Post-installation configuration utility',
    url='http://fedoraproject.org/wiki/FirstBoot',
    license = "GPLv2+",
    keywords = "firstboot inital setup",
    packages = ['inital_setup'],
    setup_requires= ['nose>=1.0'],
    test_suite = "inital_setup",
    long_description=read('README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
    ],
)
