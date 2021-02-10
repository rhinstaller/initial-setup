"""EULA spoke for the Initial Setup"""

import logging

from pyanaconda.ui.common import FirstbootOnlySpokeMixIn
from pyanaconda.ui.gui.spokes import NormalSpoke
from pykickstart.constants import FIRSTBOOT_RECONFIG

from initial_setup.product import eula_available, get_license_file_name
from initial_setup.common import LicensingCategory
from initial_setup.i18n import _, N_

log = logging.getLogger("initial-setup")

__all__ = ["EULASpoke"]


class EULASpoke(FirstbootOnlySpokeMixIn, NormalSpoke):
    """The EULA spoke"""

    builderObjects = ["eulaBuffer", "eulaWindow"]
    mainWidgetName = "eulaWindow"
    uiFile = "eula.glade"
    # The EULA spoke is self-explanatory, so just redirect its
    # help button to the Initial Setup Hub help file,
    # which covers the overall theory of Initial Setup
    # usage.
    helpFile = "InitialSetupHub.xml"

    icon = "application-certificate-symbolic"
    title = N_("_License Information")
    category = LicensingCategory
    translationDomain = "initial-setup"

    def initialize(self):
        log.debug("initializing the EULA spoke")
        NormalSpoke.initialize(self)

        self._have_eula = True
        self._eula_buffer = self.builder.get_object("eulaBuffer")
        self._agree_check_button = self.builder.get_object("agreeCheckButton")
        self._agree_label = self._agree_check_button.get_child()
        self._agree_text = self._agree_label.get_text()

        log.debug("looking for the license file")
        license_file = get_license_file_name()
        if not license_file:
            log.error("no license found")
            self._have_eula = False
            self._eula_buffer.set_text(_("No license found. Please report this "
                                         "at http://bugzilla.redhat.com"))
            return

        self._eula_buffer.set_text("")
        itr = self._eula_buffer.get_iter_at_offset(0)
        log.debug("opening the license file")
        with open(license_file, "r") as fobj:
            # insert the first line without prefixing with space
            try:
                first_line = next(fobj)
            except StopIteration:
                # nothing in the file
                return
            self._eula_buffer.insert(itr, first_line.strip())

            # EULA file is preformatted for the console, we want to let Gtk
            # format it (blank lines should be preserved)
            for line in fobj:
                stripped_line = line.strip()
                if stripped_line:
                    self._eula_buffer.insert(itr, " " + stripped_line)
                else:
                    self._eula_buffer.insert(itr, "\n\n")

    def refresh(self):
        self._agree_check_button.set_sensitive(self._have_eula)
        self._agree_check_button.set_active(self.data.eula.agreed)

    def apply(self):
        self.data.eula.agreed = self._agree_check_button.get_active()

    @property
    def completed(self):
        return not self._have_eula or self.data.eula.agreed

    @property
    def status(self):
        if not self._have_eula:
            return _("No license found")

        return _("License accepted") if self.data.eula.agreed else _("License not accepted")

    @classmethod
    def should_run(cls, environment, data):
        # the EULA spoke should only run if both are true:
        # - we are running in Initial Setup
        # - an EULA is available
        if eula_available() and FirstbootOnlySpokeMixIn.should_run(environment, data):
            # don't run if we are in reconfig mode and the EULA has already been accepted
            if data and data.firstboot.firstboot == FIRSTBOOT_RECONFIG and data.eula.agreed:
                log.debug("not running license spoke: reconfig mode & license already accepted")
                return False
            return True
        return False

    def on_check_button_toggled(self, *args):
        if self._agree_check_button.get_active():
            log.debug("license is now accepted")
            self._agree_label.set_markup("<b>%s</b>" % self._agree_text)
        else:
            log.debug("license no longer accepted")
            self._agree_label.set_markup(self._agree_text)
