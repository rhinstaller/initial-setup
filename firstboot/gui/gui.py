from pyanaconda.ui.gui import GUIObject, GraphicalUserInterface
#from .product import productName, productVersion
from .hubs import FirstbootHub
from pyanaconda.ui.gui.spokes import StandaloneSpoke
import pyanaconda.ui.gui.spokes
from pyanaconda.ui.common import collect, FirstbootSpokeMixIn
import os.path

class FirstbootGraphicalUserInterface(GraphicalUserInterface):
    """This is the standard GTK+ interface we try to steer everything to using.
       It is suitable for use both directly and via VNC.
    """
    def _list_hubs(self):
        return [FirstbootHub]

    @property
    def basemask(self):
        return "firstboot.gui"

    @property
    def paths(self):
        firstboot_path = os.path.join(os.path.dirname(__file__), "spokes")

        _anaconda_paths = GraphicalUserInterface.paths.fget(self)
        _anaconda_paths["spokes"].append((self.basemask + ".spokes.%s",
                                          os.path.join(self.basepath, "spokes")))
        _anaconda_paths["categories"].append((self.basemask + ".categories.%s",
                                          os.path.join(self.basepath, "categories")))
        return _anaconda_paths
