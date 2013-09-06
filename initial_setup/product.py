"""Module providing information about the installed product."""

RELEASE_STRING_FILE = "/etc/os-release"

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
        pass

    return ""

def is_final():
    """
    Whether it is a final release of the product or not.

    :rtype: bool

    """

    # doesn't really matter for the Initial Setup
    return True
