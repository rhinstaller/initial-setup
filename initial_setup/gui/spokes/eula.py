"""EULA spoke for the Initial Setup"""

import gettext

from gi.repository import Pango
from pyanaconda.ui.common import FirstbootOnlySpokeMixIn
from pyanaconda.ui.gui.spokes import NormalSpoke
from pyanaconda.ui.gui.categories.localization import LocalizationCategory
from pyanaconda.constants import FIRSTBOOT_ENVIRON

from initial_setup.product import get_license_file_name

_ = lambda x: gettext.ldgettext("initial-setup", x)
N_ = lambda x: x

__all__ = ["EULAspoke"]

class EULAspoke(FirstbootOnlySpokeMixIn, NormalSpoke):
    """The EULA spoke"""

    builderObjects = ["eulaBuffer", "eulaWindow"]
    mainWidgetName = "eulaWindow"
    uiFile = "eula.glade"

    icon = "application-certificate-symbolic"
    title = N_("_LICENSE INFORMATION")
    category = LocalizationCategory

    def initialize(self):
        NormalSpoke.initialize(self)

        self._have_eula = True
        self._eula_buffer = self.builder.get_object("eulaBuffer")
        self._agree_check_button = self.builder.get_object("agreeCheckButton")
        self._agree_label = self._agree_check_button.get_child()
        self._agree_text = self._agree_label.get_text()

        license_file = get_license_file_name()
        if not license_file:
            self._have_eula = False
            self._eula_buffer.set_text(_("No license found. Please report this "
                                         "at http://bugzilla.redhat.com"))
            return

        self._eula_buffer.set_text("")
        itr = self._eula_buffer.get_iter_at_offset(0)
        with open(license_file, "r") as fobj:
            for line in fobj:
                self._eula_buffer.insert(itr, line)

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

        return _("License agreed") if self.data.eula.agreed else _("License not agreed")

    def on_check_button_toggled(self, checkbutton, *args):
        if self._agree_check_button.get_active():
            self._agree_label.set_markup("<b>%s</b>" % self._agree_text)
        else:
            self._agree_label.set_markup(self._agree_text)
