import os
from pyanaconda.addons import collect_addon_paths

addon_paths = ["addons"]


addon_module_paths = collect_addon_paths(addon_paths)
print addon_module_paths

# Too bad anaconda does not have modularized logging
from pyanaconda import anaconda_log
anaconda_log.init()

# Prepare data object
from pyanaconda import kickstart
data = kickstart.AnacondaKSHandler(addon_module_paths["ks"])


# Import gui specifics
import gui

# Add to search paths
gui.FirstbootGraphicalUserInterface.update_paths(addon_module_paths)

# We need this so we can tell GI to look for overrides objects
# also in anaconda source directories
import os
import gi.overrides
for p in os.environ.get("ANACONDA_WIDGETS_OVERRIDES", "").split(":"):
    gi.overrides.__path__.insert(0, p)


g = gui.FirstbootGraphicalUserInterface(None, None, None)
        
g.setup(data)

g.run()
