import gui

# We need this so we can tell GI to look for overrides objects
# also in anaconda source directories
import os
import gi.overrides
for p in os.environ.get("ANACONDA_WIDGETS_OVERRIDES", "").split(":"):
    gi.overrides.__path__.insert(0, p)

# Too bad anaconda does not have modularized logging
from pyanaconda import anaconda_log
anaconda_log.init()

class O(object):
    pass

g = gui.FirstbootGraphicalUserInterface(None, None, None)

class O(object):
    def __init__(self, d):
        self.__dict__ = d
        
data = O({
    "rootpw": O({
        "lock": False,
        
        })
    })

g.setup(data)
g.run()

