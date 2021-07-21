"""Module providing information about the installed product."""
import logging
import os

from pyanaconda.core.configuration.anaconda import conf
from pyanaconda.core.util import get_os_release_value

log = logging.getLogger("initial-setup")


def get_product_title():
    """Get product title.

    :return: a product title
    """
    return get_os_release_value("PRETTY_NAME") or ""


def is_final():
    """Whether it is a final release of the product or not.

    :rtype: bool
    """
    # doesn't really matter for the Initial Setup
    return True


def get_license_file_name():
    """Get filename of the license file best matching current localization settings.

    :return: filename of the license file or None if no license file found
    :rtype: str or None
    """
    if not conf.license.eula:
        return None

    if not os.path.exists(conf.license.eula):
        return None

    return conf.license.eula


def eula_available():
    """Report if it looks like there is an EULA available on the system.

    :return: True if an EULA seems to be available, False otherwise
    :rtype: bool
    """
    return bool(get_license_file_name())
