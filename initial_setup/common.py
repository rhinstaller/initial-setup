"""Common methods for Initial Setup"""

import os

from pyanaconda.ui.common import collect
from pyanaconda.core.constants import FIRSTBOOT_ENVIRON
from initial_setup.i18n import _, N_
from pyanaconda.ui.categories import SpokeCategory

from initial_setup.product import eula_available

# a set of excluded console names
# - console, tty, tty0 -> these appear to be just aliases to the  default console,
#                         leaving them in would result in duplicate input on and output from
#                         the default console
# - ptmx -> pseudoterminal configuration device not intended as general user-facing console that
#           starts to block on write after some amount of characters has been written to it
# - ttyUSB0-4 -> used by some GSM modems apparently, blocks when TUI tries to use it,
#                 see rhbz#1755580 for more details about the hardware in question

TUI_EXCLUDED_CONSOLES = {"console", "tty", "tty0", "ptmx", "ttyUSB0", "ttyUSB1", "ttyUSB2", "ttyUSB3", "ttyUSB4"}

def collect_spokes(mask_paths, spoke_parent_class):
    """Return a list of all spoke subclasses that should appear for a given
       category. Look for them in files imported as module_path % basename(f)

       :param mask_paths: list of mask, path tuples to search for classes
       :type mask_paths: list of (mask, path)

       :param spoke_parent_class: Spoke parent class used for checking spoke compatibility
       :type spoke_parent_class: GUI or TUI Spoke class

       :return: list of Spoke classes belonging to category
       :rtype: list of Spoke classes

    """
    spokes = []
    for mask, path in mask_paths:

        spokes.extend(collect(mask, path,
                              lambda obj: issubclass(obj, spoke_parent_class) and obj.should_run("firstboot", None)))
    return spokes


def collectCategoriesAndSpokes(hub_instance, spoke_parent_class):
    """Collects categories and spokes to be displayed on this Hub,
       this method overrides the Anacondas implementation so that
       spokes relevant to Initial setup are collected

       :param hub_instance: an Initial Setup GUI or TUI Hub class instance
       :type hub_instance: class instance

       :param spoke_parent_class: Spoke parent class used for checking spoke compatibility
       :type spoke_parent_class: GUI or TUI Spoke class

       :return: dictionary mapping category class to list of spoke classes
       :rtype: dictionary[category class] -> [ list of spoke classes ]
    """
    ret = {}

    # Collect all the categories this hub displays, then collect all the
    # spokes belonging to all those categories.
    candidate_spokes = collect_spokes(hub_instance.paths["spokes"], spoke_parent_class)
    spokes = [spoke for spoke in candidate_spokes
              if spoke.should_run(FIRSTBOOT_ENVIRON, hub_instance.data)]

    for spoke in spokes:
        ret.setdefault(spoke.category, [])
        ret[spoke.category].append(spoke)

    return ret

def console_filter(console_name):
    """Filter out consoles we don't want to attempt running the TUI on.

    This at the moment just means console aliases, but it's possible more
    consoles will have to be added for other reasons in the guture.

    :param str console_name: console name to check
    :returns: if the console name is considered usable for IS TUI
    :rtype: bool
    """
    return console_name not in TUI_EXCLUDED_CONSOLES

def list_usable_consoles_for_tui():
    """List suitable consoles for running the Initial Setup TUI.

    We basically want to list any console a user might using,
    as we can't really be sure which console is in use or not.

    :returns: a list of console names considered usable for the IS TUI
    :rtype: list
    """
    console_names = [c for c in os.listdir("/sys/class/tty/") if console_filter(c)]
    return sorted(console_names)

def parse_os_release_lines(osreleaselines):
    """man os-release for format

       :return: dictionary mapping of line
       :rtype: dictionary
    """
    osrel = {}

    for line in osreleaselines:
        line = line.strip()
        try:
            key, sep, value = line.parition('=')
            osrel[key] = value.strip('"')
        except ValueError:
            # line.parition returned too many or too few items
            # in either case do nothing special
            pass

    return osrel

def parse_os_release_file(filename='/etc/os-release'):
    """Read os-release into a dictionary

       :return: dictionary mapping of os-release
       :rtype: dictionary
    """
    osrel = {}
    with open(filename) as osrelfil:
        osrel = parse_os_release_lines(osrelfil)

    return osrel

def os_bug_report_url(filename='/etc/os-release'):
    """Read os-release and find the BUG_REPORT_URL

       :return: url in (hopefully) RFC3986 format
       :rtype: string or None
    """
    osrel = parse_os_release_file(filename)
    return osrel.get('BUG_REPORT_URL')

def get_quit_message():
    if eula_available():
        return N_("Are you sure you want to quit the configuration process?\n"
                  "You might end up with an unusable system if you do. Unless the "
                  "License agreement is accepted, the system will be rebooted.")
    else:
        return N_("Are you sure you want to quit the configuration process?\n"
                  "You might end up with unusable system if you do.")

class LicensingCategory(SpokeCategory):

    @staticmethod
    def get_title():
        return _("LICENSING")

    @staticmethod
    def get_sort_order():
        return 100
