from pyanaconda.ui.gui.hubs import Hub
from pyanaconda.ui.gui.spokes import NormalSpoke as GUI_spoke_class
from initial_setup import product
from initial_setup import common

__all__ = ["InitialSetupMainHub"]


class InitialSetupMainHub(Hub):
    uiFile = "initial_setup.glade"
    builderObjects = ["summaryWindow"]
    mainWidgetName = "summaryWindow"
    translationDomain = "initial-setup"

    # Should we automatically go to next hub if processing is done and there are no
    # spokes on the hub ? The correct value for Initial Setup is True, due to the
    # long standing Initial Setup policy of continuing with system startup if there
    # are no spokes to be shown.
    continue_if_empty = True

    @staticmethod
    def get_screen_id():
        """Return a unique id of this UI screen."""
        return "initial-setup-summary"

    def __init__(self, *args):
        Hub.__init__(self, *args)

    def _collectCategoriesAndSpokes(self):
        return common.collectCategoriesAndSpokes(self, GUI_spoke_class)

    def _createBox(self):
        Hub._createBox(self)

        # override spokes' distribution strings set by the pyanaconda module
        for spoke in self._spokes.values():
            title = product.get_product_title().upper()
            spoke.window.set_property("distribution", title)
