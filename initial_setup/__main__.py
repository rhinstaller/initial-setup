#!/bin/python
import os
import sys
import signal
import pykickstart
import logging
from pyanaconda.users import Users
from initial_setup.post_installclass import PostInstallClass
from initial_setup import initial_setup_log
from pyanaconda import iutil
from pykickstart.constants import FIRSTBOOT_RECONFIG
from pyanaconda.localization import setup_locale_environment, setup_locale

INPUT_KICKSTART_PATH = "/root/anaconda-ks.cfg"
OUTPUT_KICKSTART_PATH = "/root/initial-setup-ks.cfg"
RECONFIG_FILE = "/etc/reconfigSys"

# set root to "/", we are now in the installed system
iutil.setSysroot("/")

signal.signal(signal.SIGINT, signal.SIG_IGN)

external_reconfig = os.path.exists(RECONFIG_FILE)

initial_setup_log.init()
log = logging.getLogger("initial-setup")

if "DISPLAY" in os.environ and os.environ["DISPLAY"]:
    mode="gui"
else:
    mode="tui"

log.debug("display mode detected: %s", mode)

if external_reconfig:
    log.debug("running in externally triggered reconfig mode")

if mode == "gui":
    # We need this so we can tell GI to look for overrides objects
    # also in anaconda source directories
    import gi.overrides
    for p in os.environ.get("ANACONDA_WIDGETS_OVERRIDES", "").split(":"):
        gi.overrides.__path__.insert(0, p)
    log.debug("GI overrides imported")

from pyanaconda.addons import collect_addon_paths

addon_paths = ["/usr/share/initial-setup/modules", "/usr/share/anaconda/addons"]

# append ADDON_PATHS dirs at the end
sys.path.extend(addon_paths)

addon_module_paths = collect_addon_paths(addon_paths, mode)
log.info("found %d addon modules:", len(addon_module_paths))
for addon_path in addon_module_paths:
    log.debug(addon_path)

# Too bad anaconda does not have modularized logging
log.debug("initializing the Anaconda log")
from pyanaconda import anaconda_log
anaconda_log.init()


# init threading before Gtk can do anything and before we start using threads
# initThreading initializes the threadMgr instance, import it afterwards
log.debug("initializing threading")
from pyanaconda.threads import initThreading
initThreading()

# initialize network logging (needed by the Network spoke that may be shown)
log.debug("initializing network logging")
from pyanaconda.network import setup_ifcfg_log
setup_ifcfg_log()

from pyanaconda import kickstart

# Construct a commandMap with the supported Anaconda's commands only
kickstart_commands = ["user",
                      "group",
                      "keyboard",
                      "lang",
                      "rootpw",
                      "timezone",
                      "logging",
                      "selinux",
                      "firewall",
                      ]

commandMap = dict((k, kickstart.commandMap[k]) for k in kickstart_commands)

# Prepare new data object
data = kickstart.AnacondaKSHandler(addon_module_paths["ks"], commandUpdates=commandMap)

kickstart_path = INPUT_KICKSTART_PATH
if os.path.exists(OUTPUT_KICKSTART_PATH):
    log.info("using kickstart from previous run for input")
    kickstart_path = OUTPUT_KICKSTART_PATH

log.info("parsing input kickstart %s", kickstart_path)
try:
    # Read the installed kickstart
    parser = kickstart.AnacondaKSParser(data)
    parser.readKickstart(kickstart_path)
    log.info("kickstart parsing done")
except pykickstart.errors.KickstartError as kserr:
    log.exception("kickstart parsing failed: %s" % kserr)
    sys.exit(1)

if external_reconfig:
    # set the reconfig flag in kickstart so that
    # relevant spokes show up
    data.firstboot.firstboot = FIRSTBOOT_RECONFIG

# Normalize the locale environment variables
if data.lang.seen:
    locale_arg = data.lang.lang
else:
    locale_arg = None
setup_locale_environment(locale_arg, prefer_environment=True)
setup_locale(os.environ['LANG'], text_mode=mode != "gui")

if mode == "gui":
    try:
        # Try to import IS gui specifics
        log.debug("trying to import GUI")
        import initial_setup.gui
    except ImportError:
        log.exception("GUI import failed, falling back to TUI")
        mode = "tui"

if mode == "gui":
    # gui already imported (see above)

    # Add addons to search paths
    initial_setup.gui.InitialSetupGraphicalUserInterface.update_paths(addon_module_paths)

    # Initialize the UI
    log.debug("initializing GUI")
    ui = initial_setup.gui.InitialSetupGraphicalUserInterface(None, None, PostInstallClass())
else:
    # Import IS gui specifics
    import initial_setup.tui

    # Add addons to search paths
    initial_setup.tui.InitialSetupTextUserInterface.update_paths(addon_module_paths)

    # Initialize the UI
    log.debug("initializing TUI")
    ui = initial_setup.tui.InitialSetupTextUserInterface(None, None, None)

# Pass the data object to user inteface
log.debug("setting up the UI")
ui.setup(data)

# Start the application
log.info("starting the UI")
ret = ui.run()

# TUI returns False if the app was ended prematurely
# all other cases return True or None
if ret == False:
    log.warning("ended prematurely in TUI")
    sys.exit(0)

# Do not execute sections that were part of the original
# anaconda kickstart file (== have .seen flag set)

sections = [data.keyboard, data.lang, data.timezone]

# data.selinux
# data.firewall

log.info("executing kickstart")
for section in sections:
    section_msg = "%s on line %d" % (repr(section), section.lineno)
    if section.seen:
        log.debug("skipping %s", section_msg)
        continue
    log.debug("executing %s", section_msg)
    section.execute(None, data, None)

# Prepare the user database tools
u = Users()

sections = [data.group, data.user, data.rootpw]
for section in sections:
    section_msg = "%s on line %d" % (repr(section), section.lineno)
    if section.seen:
        log.debug("skipping %s", section_msg)
        continue
    log.debug("executing %s", section_msg)
    section.execute(None, data, None, u)

# Configure all addons
log.info("executing addons")
data.addons.execute(None, data, None, u)

if external_reconfig:
    # prevent the reconfig flag from being written out,
    # to prevent the reconfig mode from being enabled
    # without the /etc/reconfigSys file being present
    data.firstboot.firstboot = None

# Write the kickstart data to file
log.info("writing the Initial Setup kickstart file %s", OUTPUT_KICKSTART_PATH)
with open(OUTPUT_KICKSTART_PATH, "w") as f:
    f.write(str(data))
log.info("finished writing the Initial Setup kickstart file")

# Remove the reconfig file, if any - otherwise the reconfig mode
# would start again next time the Initial Setup service is enabled
if external_reconfig and os.path.exists(RECONFIG_FILE):
    log.debug("removing the reconfig file")
    os.remove(RECONFIG_FILE)
    log.debug("the reconfig file has been removed")
