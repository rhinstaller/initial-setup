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

LOG_LEVEL_MAP = {"warning": logging.WARNING,
                 "info": logging.INFO,
                 "debug": logging.DEBUG
                 }

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

def parse_log_level(log_level_name):
    """Covert a string to log level constant.

    We only support "warning", "info" and "critical".

    :param str log_level_name: lowercase log level name
    :returns: log level constants, logging.DEBUG if log level name is unknown
    """
    return LOG_LEVEL_MAP.get(log_level_name, logging.DEBUG)

def init(stdout_log, stdout_log_level):
    """Initialize the Initial Setup logging system.

    :param bool stdout_log: if stdout log should be initialized
    :param str stdout_log_level: log level name for the stdout log
    """
    log = logging.getLogger("initial-setup")
    log.setLevel(logging.DEBUG)
    syslogHandler = InitialSetupSyslogHandler('/dev/log', SysLogHandler.LOG_LOCAL1, "initial-setup")
    syslogHandler.setLevel(logging.DEBUG)
    log.addHandler(syslogHandler)

    if stdout_log:
        # also log to stdout because someone is apparently running Initial Setup manually,
        # probably for debugging purposes
        stdoutHandler = logging.StreamHandler()
        stdoutHandler.setLevel(parse_log_level(stdout_log_level))
        stdoutHandler.setFormatter(logging.Formatter('%(levelname)s %(name)s: %(message)s'))
        log.addHandler(stdoutHandler)
