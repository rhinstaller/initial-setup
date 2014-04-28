"""Common methods for Initial Setup"""

from pyanaconda.ui.common import collect
from pyanaconda.constants import FIRSTBOOT_ENVIRON

def collect_spokes(mask_paths, spoke_parent_class):
    """Return a list of all spoke subclasses that should appear for a given
       category. Look for them in files imported as module_path % basename(f)

       :param mask_paths: list of mask, path tuples to search for classes
       :type mask_paths: list of (mask, path)

       :param spoke_parent_class: Spoke parent class used for checking spoke compatibility
       :type spoke_parent_class: GUI or TUI Spoke class

       :return: list of Spoke classes belonging to category
       :rtype: list of Spoke classes

    """
    spokes = []
    for mask, path in mask_paths:

        spokes.extend(collect(mask, path,
                              lambda obj: issubclass(obj, spoke_parent_class) and obj.should_run("firstboot", None)))
    return spokes


def collectCategoriesAndSpokes(hub_instance, spoke_parent_class):
    """Collects categories and spokes to be displayed on this Hub,
       this method overrides the Anacondas implementation so that
       spokes relevant to Initial setup are collected

       :param hub_instance: an Initial Setup GUI or TUI Hub class instance
       :type hub_instance: class instance

       :param spoke_parent_class: Spoke parent class used for checking spoke compatibility
       :type spoke_parent_class: GUI or TUI Spoke class

       :return: dictionary mapping category class to list of spoke classes
       :rtype: dictionary[category class] -> [ list of spoke classes ]
    """
    ret = {}

    # Collect all the categories this hub displays, then collect all the
    # spokes belonging to all those categories.
    candidate_spokes = collect_spokes(hub_instance.paths["spokes"], spoke_parent_class)
    spokes = [spoke for spoke in candidate_spokes
              if spoke.should_run(FIRSTBOOT_ENVIRON, hub_instance.data)]

    for spoke in spokes:
        ret.setdefault(spoke.category, [])
        ret[spoke.category].append(spoke)

    return ret
