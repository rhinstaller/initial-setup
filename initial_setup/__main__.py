#!/bin/python
import os
import sys
import pykickstart
from pyanaconda.users import Users

if "DISPLAY" in os.environ and os.environ["DISPLAY"]:
    mode="gui"
else:
    mode="tui"

if mode == "gui":
    # We need this so we can tell GI to look for overrides objects
    # also in anaconda source directories
    import gi.overrides
    for p in os.environ.get("ANACONDA_WIDGETS_OVERRIDES", "").split(":"):
        gi.overrides.__path__.insert(0, p)

# set the root path to / so the imported spokes
# know where to apply their changes
from pyanaconda import constants

# this has to stay in the form constants.ROOT_PATH so it modifies
# the scalar in anaconda, not the local copy here
constants.ROOT_PATH = "/"

from pyanaconda.addons import collect_addon_paths

addon_paths = ["/usr/share/initial-setup/modules", "/usr/share/anaconda/addons"]

# append ADDON_PATHS dirs at the end
sys.path.extend(addon_paths)

addon_module_paths = collect_addon_paths(addon_paths, mode)

# Too bad anaconda does not have modularized logging
from pyanaconda import anaconda_log
anaconda_log.init()


# init threading before Gtk can do anything and before we start using threads
# initThreading initializes the threadMgr instance, import it afterwards
from pyanaconda.threads import initThreading
initThreading()

# initialize network logging (needed by the Network spoke that may be shown)
from pyanaconda.network import setup_ifcfg_log
setup_ifcfg_log()

from pyanaconda import kickstart

# Construct a commandMap with the supported Anaconda's commands only
kickstart_commands = ["user",
                      "eula",
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

try:
    # Read the installed kickstart
    parser = kickstart.AnacondaKSParser(data)
    parser.readKickstart("/root/anaconda-ks.cfg")
except pykickstart.errors.KickstartError as kserr:
    sys.exit(1)

if mode == "gui":
    # Import IS gui specifics
    import gui

    # Add addons to search paths
    gui.InitialSetupGraphicalUserInterface.update_paths(addon_module_paths)

    # Initialize the UI
    ui = gui.InitialSetupGraphicalUserInterface(None, None, None)
else:
    # Import IS gui specifics
    import tui

    # Add addons to search paths
    tui.InitialSetupTextUserInterface.update_paths(addon_module_paths)

    # Initialize the UI
    ui = tui.InitialSetupTextUserInterface(None, None, None)

# Pass the data object to user inteface
ui.setup(data)

# Start the application
ret = ui.run()

# TUI returns False if the app was ended prematurely
# all other cases return True or None
if ret == False:
    sys.exit(0)

# Do not execute sections that were part of the original
# anaconda kickstart file (== have .seen flag set)

sections = [data.keyboard, data.lang, data.timezone]

# data.selinux
# data.firewall

for section in sections:
    if section.seen:
        continue
    section.execute(None, data, None)

# Prepare the user database tools
u = Users()

sections = [data.group, data.user, data.rootpw]
for section in sections:
    if section.seen:
        continue
    section.execute(None, data, None, u)

# Configure all addons
data.addons.execute(None, data, None, u)

# Print the kickstart data to file
with open("/root/initial-setup-ks.cfg", "w") as f:
    f.write(str(data))

