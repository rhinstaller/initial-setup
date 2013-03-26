#!/bin/python
import os
import sys
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
addon_module_paths = collect_addon_paths(addon_paths)

# Too bad anaconda does not have modularized logging
from pyanaconda import anaconda_log
anaconda_log.init()


# init threading before Gtk can do anything and before we start using threads
# initThreading initializes the threadMgr instance, import it afterwards
from pyanaconda.threads import initThreading
initThreading()

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
    
# Read the installed kickstart
parser = kickstart.AnacondaKSParser(data)
parser.readKickstart("/root/anaconda-ks.cfg")

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

# Print the kickstart file
# print data

data.keyboard.execute(None, data, None)
data.lang.execute(None, data, None)

# data.selinux.execute(None, data, None)
# data.firewall.execute(None, data, None)
# data.timezone.execute(None, data, None)

u = Users()
data.group.execute(None, data, None, u)
data.user.execute(None, data, None, u)
data.rootpw.execute(None, data, None, u)

# Configure all addons
data.addons.execute(None, data, None, u)
