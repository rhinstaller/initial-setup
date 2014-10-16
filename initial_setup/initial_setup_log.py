#
# initial_setup_log.py: Support for logging to syslog during the
#                       Initial Setup run
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
# Author(s): Martin Kolman <mkolman@redhat.com>

import logging
from logging.handlers import SysLogHandler, SYSLOG_UDP_PORT

class InitialSetupSyslogHandler(SysLogHandler):
    """A SysLogHandler subclass that makes sure the Initial Setup
    messages are easy to identify in the syslog/Journal
    """
    def __init__(self,
                 address=('localhost', SYSLOG_UDP_PORT),
                 facility=SysLogHandler.LOG_USER,
                 tag=''):
        self.tag = tag
        SysLogHandler.__init__(self, address, facility)

    def emit(self, record):
        original_msg = record.msg
        # this is needed to properly show the "initial-setup" prefix
        # for log messages in syslog/Journal
        record.msg = '%s: %s' % (self.tag, original_msg)
        SysLogHandler.emit(self, record)
        record.msg = original_msg

def init():
    """Initialize the Initial Setup logging system"""
    log = logging.getLogger("initial-setup")
    log.setLevel(logging.DEBUG)
    syslogHandler = InitialSetupSyslogHandler('/dev/log', SysLogHandler.LOG_LOCAL1, "initial-setup")
    syslogHandler.setLevel(logging.DEBUG)
    log.addHandler(syslogHandler)
