#!/bin/python

__version__ = "0.3.37"

import os
import sys
import signal
import pykickstart
import logging
import argparse
from pyanaconda.users import Users
from initial_setup.post_installclass import PostInstallClass
from initial_setup import initial_setup_log
from pyanaconda import iutil
from pykickstart.constants import FIRSTBOOT_RECONFIG
from pyanaconda.localization import setup_locale_environment, setup_locale

class InitialSetupError(Exception):
    pass

INPUT_KICKSTART_PATH = "/root/anaconda-ks.cfg"
OUTPUT_KICKSTART_PATH = "/root/initial-setup-ks.cfg"
RECONFIG_FILE = "/etc/reconfigSys"

SUPPORTED_KICKSTART_COMMANDS = ["user",
                                "group",
                                "keyboard",
                                "lang",
                                "rootpw",
                                "timezone",
                                "logging",
                                "selinux",
                                "firewall"]

# set root to "/", we are now in the installed system
iutil.setSysroot("/")

signal.signal(signal.SIGINT, signal.SIG_IGN)

external_reconfig = os.path.exists(RECONFIG_FILE)

# setup logging
log = logging.getLogger("initial-setup")

class InitialSetup(object):
    def __init__(self, gui_mode):
        """Initialize the Initial Setup internals"""
        log.debug("initializing Initial Setup")
        # True if running in graphical mode, False otherwise (text mode)
        self.gui_mode = gui_mode
        # kickstart data
        self.data = None

        # parse any command line arguments
        args = self._parse_arguments()

        # initialize logging
        initial_setup_log.init(stdout_log=not args.no_stdout_log)

        log.info("Initial Setup %s" % __version__)

        # check if we are running as root
        if os.geteuid() != 0:
            log.critical("Initial Setup needs to be run as root")
            raise InitialSetupError

        if self.gui_mode:
            log.debug("running in GUI mode")
        else:
            log.debug("running in TUI mode")

        if external_reconfig:
            log.debug("running in externally triggered reconfig mode")

        if self.gui_mode:
            # We need this so we can tell GI to look for overrides objects
            # also in anaconda source directories
            import gi.overrides
            for p in os.environ.get("ANACONDA_WIDGETS_OVERRIDES", "").split(":"):
                gi.overrides.__path__.insert(0, p)
            log.debug("GI overrides imported")

        from pyanaconda.addons import collect_addon_paths

        addon_paths = ["/usr/share/initial-setup/modules", "/usr/share/anaconda/addons"]

        # append ADDON_PATHS dirs at the end
        sys.path.extend(addon_paths)

        self._addon_module_paths = collect_addon_paths(addon_paths, self.gui_mode_id)
        log.info("found %d addon modules:", len(self._addon_module_paths))
        for addon_path in self._addon_module_paths:
            log.debug(addon_path)

        # Too bad anaconda does not have modularized logging
        log.debug("initializing the Anaconda log")
        from pyanaconda import anaconda_log
        anaconda_log.init()

        # init threading before Gtk can do anything and before we start using threads
        # initThreading initializes the threadMgr instance, import it afterwards
        log.debug("initializing threading")
        from pyanaconda.threads import initThreading
        initThreading()

        # initialize network logging (needed by the Network spoke that may be shown)
        log.debug("initializing network logging")
        from pyanaconda.network import setup_ifcfg_log
        setup_ifcfg_log()

    @property
    def gui_mode_id(self):
        """String id of the current GUI mode

        :returns: "gui" if gui_mode is True, "tui" otherwise
        :rtype str:
        """
        if self.gui_mode:
            return "gui"
        else:
            return "tui"

    def _parse_arguments(self):
        """Parse command line arguments"""
        # create an argparse instance
        parser = argparse.ArgumentParser(prog="Initial Setup",
                                         description="Initial Setup is can run during the first start of a newly installed"
                                         "system to configure it according to the needs of the user.")
        parser.add_argument("--no-stdout-log", action="store_true", default=False, help="don't log to stdout")
        parser.add_argument('--version', action='version', version=__version__)

        # parse arguments and return the result
        return parser.parse_args()

    def _load_kickstart(self):
        """Load the kickstart"""
        from pyanaconda import kickstart

        # Construct a commandMap with only the supported Anaconda's commands
        commandMap = dict((k, kickstart.commandMap[k]) for k in SUPPORTED_KICKSTART_COMMANDS)

        # Prepare new data object
        self.data = kickstart.AnacondaKSHandler(self._addon_module_paths["ks"], commandUpdates=commandMap)

        kickstart_path = INPUT_KICKSTART_PATH
        if os.path.exists(OUTPUT_KICKSTART_PATH):
            log.info("using kickstart from previous run for input")
            kickstart_path = OUTPUT_KICKSTART_PATH

        log.info("parsing input kickstart %s", kickstart_path)
        try:
            # Read the installed kickstart
            parser = kickstart.AnacondaKSParser(self.data)
            parser.readKickstart(kickstart_path)
            log.info("kickstart parsing done")
        except pykickstart.errors.KickstartError as kserr:
            log.critical("kickstart parsing failed: %s", kserr)
            log.critical("Initial Setup startup failed due to invalid kickstart file")
            raise InitialSetupError

        if external_reconfig:
            # set the reconfig flag in kickstart so that
            # relevant spokes show up
            self.data.firstboot.firstboot = FIRSTBOOT_RECONFIG

    def _setup_locale(self):
        log.debug("setting up locale")
        # Normalize the locale environment variables
        if self.data.lang.seen:
            locale_arg = self.data.lang.lang
        else:
            locale_arg = None
        setup_locale_environment(locale_arg, prefer_environment=True)
        setup_locale(os.environ['LANG'], text_mode=not self.gui_mode)

    def _apply(self):
        # Do not execute sections that were part of the original
        # anaconda kickstart file (== have .seen flag set)

        sections = [self.data.keyboard, self.data.lang, self.data.timezone]

        # data.selinux
        # data.firewall

        log.info("executing kickstart")
        for section in sections:
            section_msg = "%s on line %d" % (repr(section), section.lineno)
            if section.seen:
                log.debug("skipping %s", section_msg)
                continue
            log.debug("executing %s", section_msg)
            section.execute(None, self.data, None)

        # Prepare the user database tools
        u = Users()

        sections = [self.data.group, self.data.user, self.data.rootpw]
        for section in sections:
            section_msg = "%s on line %d" % (repr(section), section.lineno)
            if section.seen:
                log.debug("skipping %s", section_msg)
                continue
            log.debug("executing %s", section_msg)
            section.execute(None, self.data, None, u)

        # Configure all addons
        log.info("executing addons")
        self.data.addons.execute(None, self.data, None, u)

        if external_reconfig:
            # prevent the reconfig flag from being written out,
            # to prevent the reconfig mode from being enabled
            # without the /etc/reconfigSys file being present
            self.data.firstboot.firstboot = None

        # Write the kickstart data to file
        log.info("writing the Initial Setup kickstart file %s", OUTPUT_KICKSTART_PATH)
        with open(OUTPUT_KICKSTART_PATH, "w") as f:
            f.write(str(self.data))
        log.info("finished writing the Initial Setup kickstart file")

        # Remove the reconfig file, if any - otherwise the reconfig mode
        # would start again next time the Initial Setup service is enabled
        if external_reconfig and os.path.exists(RECONFIG_FILE):
            log.debug("removing the reconfig file")
            os.remove(RECONFIG_FILE)
            log.debug("the reconfig file has been removed")

    def run(self):
        """Run Initial setup

        :param bool gui_mode: if GUI should be used (TUI is the default)

        :returns: True if the IS run was successfull, False if it failed
        :rtype: bool
        """

        self._load_kickstart()
        self._setup_locale()

        if self.gui_mode:
            try:
                # Try to import IS gui specifics
                log.debug("trying to import GUI")
                import initial_setup.gui
            except ImportError:
                log.exception("GUI import failed, falling back to TUI")
                self.gui_mode = False

        if self.gui_mode:
            # gui already imported (see above)

            # Add addons to search paths
            initial_setup.gui.InitialSetupGraphicalUserInterface.update_paths(self._addon_module_paths)

            # Initialize the UI
            log.debug("initializing GUI")
            ui = initial_setup.gui.InitialSetupGraphicalUserInterface(None, None, PostInstallClass())
        else:
            # Import IS gui specifics
            import initial_setup.tui

            # Add addons to search paths
            initial_setup.tui.InitialSetupTextUserInterface.update_paths(self._addon_module_paths)

            # Initialize the UI
            log.debug("initializing TUI")
            ui = initial_setup.tui.InitialSetupTextUserInterface(None, None, None)

        # Pass the data object to user inteface
        log.debug("setting up the UI")
        ui.setup(self.data)

        # Start the application
        log.info("starting the UI")
        ret = ui.run()

        # TUI returns False if the app was ended prematurely
        # all other cases return True or None
        if ret is False:
            log.warning("ended prematurely in TUI")
            return True

        # apply changes
        self._apply()

        # and we are done
        return True
