#!/bin/python
import os

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
from pyanaconda.constants import ROOT_PATH
ROOT_PATH = "/"

from pyanaconda.addons import collect_addon_paths

addon_paths = ["/usr/share/initial-setup/modules", "/usr/share/anaconda/addons"]
addon_module_paths = collect_addon_paths(addon_paths)

# Too bad anaconda does not have modularized logging
from pyanaconda import anaconda_log
anaconda_log.init()

# Prepare new data object
from pyanaconda import kickstart
data = kickstart.AnacondaKSHandler(addon_module_paths["ks"])

# Replace storage commands by Dummy objects
# TODO

# Read the installed kickstart
parser = kickstart.AnacondaKSParser(data)
parser.readKickstart("anaconda-ks.cfg")

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
ui.run()

# Print the kickstart file
print data
