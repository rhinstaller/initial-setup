import gui

# We need this so we can tell GI to look for overrides objects
# also in anaconda source directories
import os
import gi.overrides
for p in os.environ.get("ANACONDA_WIDGETS_OVERRIDES", "").split(":"):
    gi.overrides.__path__.insert(0, p)
    
class O(object):
    pass

g = gui.FirstbootGraphicalUserInterface(None, None, None)
data = O()
g.setup(data)
g.run()

