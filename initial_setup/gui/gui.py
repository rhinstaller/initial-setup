from pyanaconda.ui.gui import QuitDialog, GraphicalUserInterface
from initial_setup.product import product_title, is_final
from .hubs import InitialSetupMainHub
import os
from gi.repository import Gdk, Gtk
import gettext
from di import inject, usesclassinject

# localization
_ = lambda x: gettext.ldgettext("initial-setup", x)
N_ = lambda x: x

class InitialSetupQuitDialog(QuitDialog):
    MESSAGE = N_("Are you sure you want to quit the configuration process?\n"
                 "You might end up with an unusable system if you do. Unless the "
                 "License agreement is accepted, the system will be rebooted.")

    def run(self):
        """Wrap the parent run method to change behavior of the Quit button.

        If the Quit button is clicked the QuitDialog will have rc == 1.
        Unfortunately (from the Initial Setup point of view) GraphicalUserInterface
        calls sys.exit(0) if QuitDialog rc == 1 - unlike Anaconda Initial Setup
        still has some housekeeping to do even if it is told to Quit.

        So we don't propagate the rc value back to GraphicalUserInterface
        but instead just quit the GTK mainloop. This continues the execution
        of the Initial Setup run script, which can do the necessary housekeeping,
        such as checking if the system should be rebooted if the EULA is not accepted.

        Eventually a more clean solution could be to add a property to QuitDialog
        that GraphicalUserInterface would check and quite the GTK main loop instead of
        running sys.exit(0).
        """
        rc = super(InitialSetupQuitDialog, self).run()
        if rc == 1:
            Gtk.main_quit()

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
        self.mainWindow.set_title("")

    def _list_hubs(self):
        return [InitialSetupMainHub]

    basemask = "initial_setup.gui"
    basepath = os.path.dirname(__file__)
    paths = GraphicalUserInterface.paths + {
        "spokes": [(basemask + ".spokes.%s", os.path.join(basepath, "spokes"))],
        "categories": [(basemask + ".categories.%s", os.path.join(basepath, "categories"))],
        }
