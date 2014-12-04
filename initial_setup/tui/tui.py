from pyanaconda.ui.tui import TextUserInterface
from initial_setup.product import product_title, is_final
from .hubs import InitialSetupMainHub
import os
import gettext
from di import inject, usesclassinject

# localization
_ = lambda x: gettext.ldgettext("initial-setup", x)
N_ = lambda x: x

QUIT_MESSAGE = N_("Are you sure you want to quit the configuration process?\n"
                  "You might end up with unusable system if you do.")

@inject(product_title = product_title, is_final = is_final)
class InitialSetupTextUserInterface(TextUserInterface):
    """This is the main text based firstboot interface. It inherits from
       anaconda to make the look & feel as similar as possible.
    """

    ENVIRONMENT = "firstboot"

    @usesclassinject
    def __init__(self, storage, payload, instclass):
        TextUserInterface.__init__(self, storage, payload, instclass,
                                         product_title, is_final, quitMessage = QUIT_MESSAGE)

    def _list_hubs(self):
        return [InitialSetupMainHub]

    basemask = "firstboot.tui"
    basepath = os.path.dirname(__file__)
    paths = TextUserInterface.paths + {
        "spokes": [(basemask + ".spokes.%s", os.path.join(basepath, "spokes"))],
        "categories": [(basemask + ".categories.%s", os.path.join(basepath, "categories"))],
        }

