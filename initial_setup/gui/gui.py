from pyanaconda.ui.gui import QuitDialog, GraphicalUserInterface
from initial_setup.product import product_title, is_final, eula_available
from .hubs import InitialSetupMainHub
import os
from gi.repository import Gdk
import gettext

# localization
_ = lambda x: gettext.ldgettext("initial-setup", x)
N_ = lambda x: x

def get_quit_message():
    if eula_available():
        return N_("Are you sure you want to quit the configuration process?\n"
                  "You might end up with an unusable system if you do. Unless the "
                  "License agreement is accepted, the system will be rebooted.")
    else:
        return N_("Are you sure you want to quit the configuration process?\n"
                  "You might end up with unusable system if you do.")

class InitialSetupQuitDialog(QuitDialog):
    MESSAGE = get_quit_message()

class InitialSetupGraphicalUserInterface(GraphicalUserInterface):
    """This is the main Gtk based firstboot interface. It inherits from
       anaconda to make the look & feel as similar as possible.
    """

    screenshots_directory = "/tmp/initial-setup-screenshots"

    def __init__(self, storage, payload, instclass):
        GraphicalUserInterface.__init__(self, storage, payload, instclass,
                                        product_title, is_final,
                                        quitDialog = InitialSetupQuitDialog)
        self.mainWindow.set_title("")

    def _list_hubs(self):
        return [InitialSetupMainHub]

    basemask = "initial_setup.gui"
    basepath = os.path.dirname(__file__)
    paths = GraphicalUserInterface.paths + {
        "spokes": [(basemask + ".spokes.%s", os.path.join(basepath, "spokes"))],
        "categories": [(basemask + ".categories.%s", os.path.join(basepath, "categories"))],
        }

