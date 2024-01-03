#!/usr/bin/python3
# Setup file for initial-setup
#
# Copyright (C) 2020  Red Hat, Inc.
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

import os
from glob import glob
from setuptools import setup, find_packages


data_files = [('/usr/lib/systemd/system', glob('systemd/*.service')),
              ('/etc/initial-setup/conf.d', glob('data/*.conf')),
              ('/etc/pam.d', glob('pam/*')),
              ('/usr/libexec/initial-setup/',
              ["scripts/run-initial-setup", "scripts/firstboot-windowmanager",
               "scripts/initial-setup-text", "scripts/initial-setup-graphical",
               "scripts/run-gui-backend.guixorg", "scripts/run-gui-backend.guiweston",
               "scripts/run-gui-backend",  # symlink to the default backend
               "scripts/reconfiguration-mode-enabled"]),
              ('/usr/share/doc/initial-setup/', ["ChangeLog"])]

# add the firstboot start script for s390 architectures
if os.uname()[4].startswith('s390'):
    data_files.append(('/etc/profile.d', ['scripts/s390/initial-setup.sh']))
    data_files.append(('/etc/profile.d', ['scripts/s390/initial-setup.csh']))

with open("README.rst", "r") as f:
    long_description = f.read()

setup(name="initial-setup",
      version="0.3.99",
      author="Martin Kolman",
      author_email="mkolman@redhat.com",
      description='Post-installation configuration utility',
      long_description=long_description,
      long_description_content_type="text/x-rst",
      url='https://fedoraproject.org/wiki/InitialSetup',
      license="GPLv2+",
      keywords="firstboot initial setup",
      packages=find_packages(),
      package_data={
          "": ["*.glade"]
      },
      data_files=data_files,
      test_suite="initial_setup",
      classifiers=[
          "Development Status :: 3 - Alpha",
          "Environment :: X11 Applications :: GTK",
          "Environment :: Console",
          "Intended Audience :: System Administrators",
          "Topic :: System :: Systems Administration",
          "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
          "Programming Language :: Python :: 3",
      ],
)
