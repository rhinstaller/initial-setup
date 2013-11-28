from pyanaconda.constants import FIRSTBOOT_ENVIRON
from pyanaconda.ui.tui.hubs import TUIHub
from initial_setup import product
import gettext

__all__ = ["InitialSetupMainHub"]

# localization
_ = lambda x: gettext.ldgettext("initial-setup", x)
N_ = lambda x: x

class InitialSetupMainHub(TUIHub):
    categories = ["user", "localization"]

    prod_title = product.product_title()
    if prod_title:
        title = _("Initial setup of %(product)s") % {"product": prod_title}
    else:
        title = _("Initial setup")

    def __init__(self, *args):
        TUIHub.__init__(self, *args)
        self._environs = [FIRSTBOOT_ENVIRON]
