from pyanaconda.ui.tui.hubs import TUIHub
from pyanaconda.ui.tui.spokes import NormalSpoke as TUI_spoke_class
from initial_setup import product
from initial_setup import common
import gettext

__all__ = ["InitialSetupMainHub"]

# localization
_ = lambda x: gettext.ldgettext("initial-setup", x)
N_ = lambda x: x

class InitialSetupMainHub(TUIHub):
    categories = ["user", "localization"]

    prod_title = product.product_title()
    if prod_title:
        title = N_("Initial setup of %(product)s") % {"product": prod_title}
    else:
        title = N_("Initial setup")

    def __init__(self, *args):
        TUIHub.__init__(self, *args)

    def _collectCategoriesAndSpokes(self):
        return common.collectCategoriesAndSpokes(self, TUI_spoke_class)
