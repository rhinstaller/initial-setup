"""Module providing information about the installed product."""
import logging

from pyanaconda.localization import find_best_locale_match
from pyanaconda.core.constants import DEFAULT_LANG
import os
import glob

RELEASE_STRING_FILE = "/etc/os-release"
LICENSE_FILE_GLOB = "/usr/share/redhat-release*/EULA*"

log = logging.getLogger("initial-setup")


def product_title():
    """
    Get product title.

    :return: product title
    :rtype: str

    """

    try:
        with open(RELEASE_STRING_FILE, "r") as fobj:
            for line in fobj:
                (key, _eq, value) = line.strip().partition("=")
                if not key or not _eq or not value:
                    continue
                if key == "PRETTY_NAME":
                    return value.strip('"')
    except IOError:
        log.exception("failed to check the release string file")

    return ""


def is_final():
    """
    Whether it is a final release of the product or not.

    :rtype: bool

    """

    # doesn't really matter for the Initial Setup
    return True


def get_license_file_name():
    """Get filename of the license file best matching current localization settings.

    :return: filename of the license file or None if no license file found
    :rtype: str or None
    """

    all_eulas = glob.glob(LICENSE_FILE_GLOB)
    non_localized_eulas = []
    langs = set()
    for eula in all_eulas:
        if "EULA_" in eula:
            # license file for a specific locale
            lang = eula.rsplit("EULA_", 1)[1]
            if lang:
                langs.add(lang)
        else:
            non_localized_eulas.append(eula)

    best_lang = find_best_locale_match(os.environ["LANG"], langs)
    if not best_lang:
        # nothing found for the current language, try the default one
        best_lang = find_best_locale_match(DEFAULT_LANG, langs)

    if not best_lang:
        # nothing found even for the default language, use non-localized or None
        if non_localized_eulas:
            best_eula = non_localized_eulas[0]
        else:
            return None
    else:
        # use first of the best-matching EULA files (there should be only one)
        best_eula = glob.glob(LICENSE_FILE_GLOB + ("_%s" % best_lang))[0]

    return best_eula


def eula_available():
    """ Report if it looks like there is an EULA available on the system.

    :return: True if an EULA seems to be available, False otherwise
    :rtype: bool
    """
    return bool(get_license_file_name())
