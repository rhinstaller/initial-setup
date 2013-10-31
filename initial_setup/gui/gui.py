from pyanaconda.ui.gui import QuitDialog, GUIObject, GraphicalUserInterface
from initial_setup.product import product_title, is_final
from .hubs import InitialSetupMainHub
from pyanaconda.ui.gui.spokes import StandaloneSpoke
import pyanaconda.ui.gui.spokes
from pyanaconda.ui.common import collect, FirstbootSpokeMixIn
import os
from gi.repository import Gdk
import logging
import gettext
from di import inject, usesclassinject

# localization
_ = lambda x: gettext.ldgettext("initial-setup", x)
N_ = lambda x: x

class InitialSetupQuitDialog(QuitDialog):
    MESSAGE = N_("Are you sure you want to quit the configuration process?\n"
                 "You might end up with an unusable system if you do. Unless the "
                 "License agreement is accepted, the system will be rebooted.")

@inject(Gdk, product_title = product_title, is_final = is_final)
class InitialSetupGraphicalUserInterface(GraphicalUserInterface):
    """This is the main Gtk based firstboot interface. It inherits from
       anaconda to make the look & feel as similar as possible.
    """

    screenshots_directory = "/tmp/initial-setup-screenshots"

    @usesclassinject
    def __init__(self, storage, payload, instclass):
        GraphicalUserInterface.__init__(self, storage, payload, instclass,
                                        product_title, is_final,
                                        quitDialog = InitialSetupQuitDialog)

    def _list_hubs(self):
        return [InitialSetupMainHub]

    basemask = "initial_setup.gui"
    basepath = os.path.dirname(__file__)
    paths = GraphicalUserInterface.paths + {
        "spokes": [(basemask + ".spokes.%s", os.path.join(basepath, "spokes"))],
        "categories": [(basemask + ".categories.%s", os.path.join(basepath, "categories"))],
        }

