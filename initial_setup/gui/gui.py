from pyanaconda.ui.gui import QuitDialog, GraphicalUserInterface
from initial_setup.product import product_title, is_final
from initial_setup.common import get_quit_message
from initial_setup.i18n import _, N_
from .hubs import InitialSetupMainHub
import os
from gi.repository import Gdk

class InitialSetupQuitDialog(QuitDialog):
    MESSAGE = get_quit_message()

class InitialSetupGraphicalUserInterface(GraphicalUserInterface):
    """This is the main Gtk based firstboot interface. It inherits from
       anaconda to make the look & feel as similar as possible.
    """

    screenshots_directory = "/tmp/initial-setup-screenshots"

    def __init__(self):
        GraphicalUserInterface.__init__(self, None, None, product_title, is_final,
                                        quitDialog=InitialSetupQuitDialog)
        self.mainWindow.set_title("")

    def _list_hubs(self):
        return [InitialSetupMainHub]

    basemask = "initial_setup.gui"
    basepath = os.path.dirname(__file__)
    paths = GraphicalUserInterface.paths + {
        "spokes": [(basemask + ".spokes.%s", os.path.join(basepath, "spokes"))],
        "categories": [(basemask + ".categories.%s", os.path.join(basepath, "categories"))],
        }

