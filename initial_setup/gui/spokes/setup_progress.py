#
# Copyright (C) 2011-2013  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
import logging

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from initial_setup import InitialSetupTask
from initial_setup.gui.hubs import InitialSetupMainHub
from pyanaconda.core.i18n import _, C_
from pyanaconda.modules.common.constants.services import USERS
from pyanaconda.product import productName
from pyanaconda.core import util
from pyanaconda.core.configuration.anaconda import conf
from pyanaconda.core.constants import IPMI_FINISHED
from pyanaconda.ui.common import FirstbootOnlySpokeMixIn
from pyanaconda.ui.gui.spokes import StandaloneSpoke
from pyanaconda.ui.gui.utils import gtk_call_once

log = logging.getLogger("initial-setup")

__all__ = ["ProgressSpoke"]


class ProgressSpoke(FirstbootOnlySpokeMixIn, StandaloneSpoke):
    """
       .. inheritance-diagram:: ProgressSpoke
          :parts: 3
    """

    builderObjects = ["progressWindow"]
    mainWidgetName = "progressWindow"
    uiFile = "setup_progress.glade"
    postForHub = InitialSetupMainHub

    @staticmethod
    def get_screen_id():
        """Return a unique id of this UI screen."""
        return "installation-progress"

    def __init__(self, data, storage, payload):
        super().__init__(data, storage, payload)
        self._progressBar = self.builder.get_object("progressBar")
        self._progressLabel = self.builder.get_object("progressLabel")
        self._progressNotebook = self.builder.get_object("progressNotebook")
        self._spinner = self.builder.get_object("progressSpinner")
        self._task = None

        # Record if groups, users or root password has been set before Initial Setup
        # has been started, so that we don't trample over existing configuration.
        log.info("collecting initial state")
        users_proxy = USERS.get_proxy()
        self._groups_already_configured = bool(users_proxy.Groups)
        self._users_already_configured = bool(users_proxy.Users)
        self._root_password_already_configured = users_proxy.IsRootPasswordSet

    @property
    def completed(self):
        """This spoke is never completed, initially."""
        return False

    def apply(self):
        """There is nothing to apply."""
        pass

    def _on_installation_done(self):
        log.debug("The initial setup has finished.")

        # Stop the spinner.
        gtk_call_once(self._spinner.stop)
        gtk_call_once(self._spinner.hide)

        # Finish the installation task. Re-raise tracebacks if any.
        try:
            self._task.finish()
        except Exception as e:
            log.exception("Initial setup failed")
            self.showErrorMessageHelper(str(e))

        util.ipmi_report(IPMI_FINISHED)

        if conf.license.eula:
            self.set_warning(_("Use of this product is subject to the license agreement "
                               "found at %s") % conf.license.eula)
            self.window.show_all()

        # Show the reboot message.
        self._progressNotebook.set_current_page(1)

        # Enable the continue button.
        self.window.set_may_continue(True)

        # Hide the quit button.
        quit_button = self.window.get_quit_button()
        quit_button.hide()

        # automatically close; if there was an error, showErrorMessageHelper
        # already waited for the user to click ok
        self.window.emit("continue-clicked")

    def initialize(self):
        super().initialize()
        # Disable the continue button.
        self.window.set_may_continue(False)

        # Set the label of the continue button.
        continue_label = C_("GUI|Progress", "_Finish Installation")

        continue_button = self.window.get_continue_button()
        continue_button.set_label(continue_label)

        # Set the reboot label.
        continue_text = _(
            "%s is now successfully installed and ready for you to use!\n"
            "Go ahead and quit the application to start using it!"
        ) % productName

        label = self.builder.get_object("rebootLabel")
        label.set_text(continue_text)

        # Don't show the reboot message.
        self._progressNotebook.set_current_page(0)

    def refresh(self):
        from pyanaconda.installation import RunInstallationTask
        super().refresh()

        # Initialize the progress bar.
        gtk_call_once(self._progressBar.set_fraction, 0.0)

        # Start the installation task.
        self._task = InitialSetupTask(
            groups_already_configured=self._groups_already_configured,
            users_already_configured=self._users_already_configured,
            root_password_already_configured=self._root_password_already_configured,
        )
        self._task.progress_changed_signal.connect(
            self._on_progress_changed
        )
        self._task.stopped_signal.connect(
            self._on_installation_done
        )
        self._task.start()

        # Start the spinner.
        gtk_call_once(self._spinner.start)

        log.debug("The installation has started.")

    def showErrorMessageHelper(self, text):
        dlg = Gtk.MessageDialog(title="Error", message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK, text=text)
        dlg.set_position(Gtk.WindowPosition.CENTER)
        dlg.set_modal(True)
        dlg.set_transient_for(self.main_window)
        dlg.run()
        dlg.destroy()

    def _on_progress_changed(self, step, message):
        """Handle a new progress report."""
        if message:
            gtk_call_once(self._progressLabel.set_text, message)

        if self._task.steps > 0:
            gtk_call_once(self._progressBar.set_fraction, step/self._task.steps)
