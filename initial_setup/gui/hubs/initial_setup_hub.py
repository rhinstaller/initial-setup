from pyanaconda.constants import FIRSTBOOT_ENVIRON
from pyanaconda.ui.gui.hubs import Hub
from pyanaconda.ui.gui.spokes import Spoke
from pyanaconda.ui.common import collect
from initial_setup import product

__all__ = ["InitialSetupMainHub"]

def collect_spokes(mask_paths):
    """Return a list of all spoke subclasses that should appear for a given
       category. Look for them in files imported as module_path % basename(f)

       :param mask_paths: list of mask, path tuples to search for classes
       :type mask_paths: list of (mask, path)

       :return: list of Spoke classes belonging to category
       :rtype: list of Spoke classes

    """
    spokes = []
    for mask, path in mask_paths:
        spokes.extend(collect(mask, path,
                              lambda obj: issubclass(obj, Spoke) and obj.should_run("firstboot", None)))

    return spokes


class InitialSetupMainHub(Hub):
    uiFile = "initial_setup.glade"
    builderObjects = ["summaryWindow"]
    mainWidgetName = "summaryWindow"

    def __init__(self, *args):
        Hub.__init__(self, *args)
        self._environs = [FIRSTBOOT_ENVIRON]

    def _collectCategoriesAndSpokes(self):
        """collects categories and spokes to be displayed on this Hub

           :return: dictionary mapping category class to list of spoke classes
           :rtype: dictionary[category class] -> [ list of spoke classes ]
        """

        ret = {}

        # Collect all the categories this hub displays, then collect all the
        # spokes belonging to all those categories.
        candidate_spokes = collect_spokes(self.paths["spokes"])
        spokes = [spoke for spoke in candidate_spokes \
                        if spoke.should_run(FIRSTBOOT_ENVIRON, self.data)]

        for spoke in spokes:
            ret.setdefault(spoke.category, [])
            ret[spoke.category].append(spoke)

        return ret

    def _createBox(self):
        Hub._createBox(self)

        # override spokes' distribution strings set by the pyanaconda module
        for spoke in self._spokes.itervalues():
            spoke.window.set_property("distribution",
                                      product.product_title().upper())


    @property
    def continueButton(self):
        return self.builder.get_object("continueButton")

    @property
    def quitButton(self):
        return self.builder.get_object("quitButton")
