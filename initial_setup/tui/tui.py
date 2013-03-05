from pyanaconda.ui.tui import TextUserInterface
#from .product import productName, productVersion
from .hubs import InitialSetupMainHub
from pyanaconda.ui.tui.spokes import StandaloneSpoke
import pyanaconda.ui.tui.spokes
from pyanaconda.ui.common import collect, FirstbootSpokeMixIn
import os
import logging
from di import inject, usesclassinject

# localization
_ = lambda t: t
N_ = lambda t: t

productTitle = lambda: "Initial Setup of Fedora"
isFinal = lambda: False

QUIT_MESSAGE = N_("Are you sure you want to quit the configuration process?\n"
                  "You might end up with unusable system if you do.")

@inject(productTitle = productTitle, isFinal = isFinal)
class InitialSetupTextUserInterface(TextUserInterface):
    """This is the main text based firstboot interface. It inherits from
       anaconda to make the look & feel as similar as possible.
    """
    
    @usesclassinject
    def __init__(self, storage, payload, instclass):
        TextUserInterface.__init__(self, storage, payload, instclass,
                                         productTitle, isFinal, quitMessage = QUIT_MESSAGE)
        
    def _list_hubs(self):
        return [InitialSetupMainHub]

    basemask = "firstboot.tui"
    basepath = os.path.dirname(__file__)
    paths = TextUserInterface.paths + {
        "spokes": [(basemask + ".spokes.%s", os.path.join(basepath, "spokes"))],
        "categories": [(basemask + ".categories.%s", os.path.join(basepath, "categories"))],
        }

