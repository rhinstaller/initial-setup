import os

# We need this so we can tell GI to look for overrides objects
# also in anaconda source directories
import gi.overrides
for p in os.environ.get("ANACONDA_WIDGETS_OVERRIDES", "").split(":"):
    gi.overrides.__path__.insert(0, p)

from pyanaconda.addons import collect_addon_paths

addon_paths = ["/usr/share/inital-setup/modules", "/usr/share/anaconda/addons"]
addon_module_paths = collect_addon_paths(addon_paths)

# Too bad anaconda does not have modularized logging
from pyanaconda import anaconda_log
anaconda_log.init()

# Prepare new data object
from pyanaconda import kickstart
data = kickstart.AnacondaKSHandler(addon_module_paths["ks"])

# Import IS gui specifics
import gui

# Add addons to search paths
gui.InitalSetupGraphicalUserInterface.update_paths(addon_module_paths)

# Initialize the UI
g = gui.InitalSetupGraphicalUserInterface(None, None, None)
g.setup(data)

# Start the application
g.run()
