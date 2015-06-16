#
# Simple post-install class
#
# Copyright (C) 2014  Red Hat, Inc.  All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from pyanaconda.installclass import BaseInstallClass

class PostInstallClass(BaseInstallClass):
    help_placeholder = "RHEL7Placeholder.html"
    help_placeholder_with_links = "RHEL7PlaceholderWithLinks.html"

    def __init__(self):
        BaseInstallClass.__init__(self)
