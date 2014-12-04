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

INPUT_KICKSTART_PATH = "/root/anaconda-ks.cfg"
OUTPUT_KICKSTART_PATH = "/root/initial-setup-ks.cfg"

# set root to "/", we are now in the installed system
iutil.setSysroot("/")

signal.signal(signal.SIGINT, signal.SIG_IGN)

initial_setup_log.init()
log = logging.getLogger("initial-setup")

if "DISPLAY" in os.environ and os.environ["DISPLAY"]:
    mode="gui"
else:
    mode="tui"

log.debug("display mode detected: %s", mode)

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

log.info("parsing input kickstart %s", INPUT_KICKSTART_PATH)
try:
    # Read the installed kickstart
    parser = kickstart.AnacondaKSParser(data)
    parser.readKickstart(INPUT_KICKSTART_PATH)
    log.info("kickstart parsing done")
except pykickstart.errors.KickstartError as kserr:
    log.exception("kickstart parsing failed")
    sys.exit(1)

if mode == "gui":
    try:
        # Try to import IS gui specifics
        log.debug("trying to import GUI")
        import initial_setup.gui
    except ImportError:
        log.error("GUI import failed, falling back to TUI")
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

# Write the kickstart data to file
log.info("writing the Initial Setup kickstart file %s", OUTPUT_KICKSTART_PATH)
with open(OUTPUT_KICKSTART_PATH, "w") as f:
    f.write(str(data))
log.info("finished writing the Initial Setup kickstart file")
