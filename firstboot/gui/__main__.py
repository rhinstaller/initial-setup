import os

addon_paths = ["addons"]

def collect_plugins(addon_paths, ui = "gui"):
    # collect all applicable addon paths from
    # for p in addon_paths: <p>/<plugin id>/ks/*.(py|so)
    # and register them under <plugin id> name

    module_paths = {
        "spokes": [],
        "ks": [],
        "categories": []
        }
    
    for path in addon_paths:
        try:
            files = os.listdir(path)
        except OSError:
            files = []
                
        for addon_id in files:
            addon_ks_path = os.path.join(path, addon_id, "ks")
            if os.path.isdir(addon_ks_path):
                module_paths["ks"].append(("anaconda.addon.%s.ks.%%s" % addon_id, addon_ks_path))

            addon_spoke_path = os.path.join(path, addon_id, ui, "spokes")
            if os.path.isdir(addon_spoke_path):
                module_paths["spokes"].append(("anaconda.addon.%s.spokes.%%s" % addon_id, addon_spoke_path))

            addon_category_path = os.path.join(path, addon_id, ui, "categories")
            if os.path.isdir(addon_spoke_path):
                module_paths["categories"].append(("anaconda.addon.%s.categories.%%s" % addon_id, addon_category_path))

    return module_paths

addon_module_paths = collect_plugins(addon_paths)
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
