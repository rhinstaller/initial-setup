__version__ = "0.3.93"

import os
import sys
import signal
import pykickstart
import logging
import argparse
import traceback
import atexit

from initial_setup.product import eula_available
from initial_setup import initial_setup_log

from pyanaconda.core.dbus import DBus
from pyanaconda.core.util import get_os_release_value
from pyanaconda.localization import setup_locale_environment, setup_locale
from pyanaconda.core.constants import FIRSTBOOT_ENVIRON, SETUP_ON_BOOT_RECONFIG, \
    SETUP_ON_BOOT_DEFAULT
from pyanaconda.flags import flags
from pyanaconda.core.startup.dbus_launcher import AnacondaDBusLauncher
from pyanaconda.modules.common.task import sync_run_task
from pyanaconda.modules.common.constants.services import BOSS, LOCALIZATION, TIMEZONE, USERS, \
    SERVICES, NETWORK
from pyanaconda.modules.common.structures.kickstart import KickstartReport


class InitialSetupError(Exception):
    pass


INPUT_KICKSTART_PATH = "/root/anaconda-ks.cfg"
OUTPUT_KICKSTART_PATH = "/root/initial-setup-ks.cfg"
RECONFIG_FILES = ["/etc/reconfigSys", "/.unconfigured"]

SUPPORTED_KICKSTART_COMMANDS = ["user",
                                "group",
                                "keyboard",
                                "lang",
                                "rootpw",
                                "timezone",
                                "selinux",
                                "firewall"]

# set the environment so that spokes can behave accordingly
flags.environs = [FIRSTBOOT_ENVIRON]

signal.signal(signal.SIGINT, signal.SIG_IGN)

# setup logging
log = logging.getLogger("initial-setup")

logging_initialized = False


def log_to_journal(message, priority=3):
    """A quick-and-dirty direct Journal logger.

    A quick-and-dirty direct Journal logger used to log errors that occur
    before the normal Python logging system is setup and connected to Journal.

    :param str message: message to send to Journal
    :param int priority: message priority (2 - critical, 3 - error, 4 - warning, 5 - notice, 6 - info)
    """
    os.system('echo "%s" | systemd-cat -t initial-setup -p %s' % (message, priority))


def log_exception(*exception_info):
    exception_text = "".join(traceback.format_exception(*exception_info))
    error_message = "Initial Setup crashed due to unhandled exception:\n%s" % exception_text
    if logging_initialized:
        log.error(error_message)
    else:
        log_to_journal(error_message)


sys.excepthook = log_exception


class InitialSetup(object):
    def __init__(self, gui_mode):
        """Initialize the Initial Setup internals"""
        log.debug("initializing Initial Setup")
        # True if running in graphical mode, False otherwise (text mode)
        self.gui_mode = gui_mode
        # kickstart data
        self.data = None
        # reboot on quit flag
        self._reboot_on_quit = False

        # parse any command line arguments
        self._args = self._parse_arguments()

        # initialize logging
        initial_setup_log.init(stdout_log=not self._args.no_stdout_log)
        global logging_initialized
        logging_initialized = True

        log.info("Initial Setup %s" % __version__)

        # check if we are running as root
        if os.geteuid() != 0:
            log.critical("Initial Setup needs to be run as root")
            raise InitialSetupError

        # load configuration files
        from pyanaconda.core.configuration.base import ConfigurationError
        from pyanaconda.core.configuration.anaconda import conf
        try:
            conf.set_from_detected_profile(
                get_os_release_value("ID")
            )
        except ConfigurationError as e:
            log.warning(str(e))

        conf.set_from_files(["/etc/initial-setup/conf.d/"])

        if self.gui_mode:
            log.debug("running in GUI mode")
        else:
            log.debug("running in TUI mode")

        self._external_reconfig = False

        # check if the reconfig mode should be enabled
        # by checking if at least one of the reconfig
        # files exist
        for reconfig_file in RECONFIG_FILES:
            if os.path.exists(reconfig_file):
                self.external_reconfig = True
                log.debug("reconfig trigger file found: %s", reconfig_file)

        if self.external_reconfig:
            log.debug("running in externally triggered reconfig mode")

        if self.gui_mode:
            # We need this so we can tell GI to look for overrides objects
            # also in anaconda source directories
            import gi.overrides
            for p in os.environ.get("ANACONDA_WIDGETS_OVERRIDES", "").split(":"):
                gi.overrides.__path__.insert(0, p)
            log.debug("GI overrides imported")

        from pyanaconda.ui.lib.addons import collect_addon_ui_paths
        addon_paths = ["/usr/share/initial-setup/modules", "/usr/share/anaconda/addons"]

        # append ADDON_PATHS dirs at the end
        sys.path.extend(addon_paths)

        self._addon_module_paths = collect_addon_ui_paths(addon_paths, self.gui_mode_id)
        log.info("found %d addon modules:", len(self._addon_module_paths))
        for addon_path in self._addon_module_paths:
            log.debug(addon_path)

        # Too bad anaconda does not have modularized logging
        log.debug("initializing the Anaconda log")
        from pyanaconda import anaconda_logging
        anaconda_logging.init(write_to_journal=True)

        # create class for launching our dbus session
        self._dbus_launcher = AnacondaDBusLauncher()

        # group, user, root password set-before tracking
        self._groups_already_configured = False
        self._users_already_configured = False
        self._root_password_already_configured = False

    @property
    def external_reconfig(self):
        """External reconfig status.

        Reports if external (eq. not triggered by kickstart) has been enabled.

        :returns: True if external reconfig mode has been enabled, else False.
        :rtype: bool
        """
        return self._external_reconfig

    @external_reconfig.setter
    def external_reconfig(self, value):
        self._external_reconfig = value

    @property
    def gui_mode_id(self):
        """String id of the current GUI mode

        :returns: "gui" if gui_mode is True, "tui" otherwise
        :rtype: str
        """
        if self.gui_mode:
            return "gui"
        else:
            return "tui"

    @property
    def reboot_on_quit(self):
        # should the machine be rebooted once Initial Setup quits
        return self._reboot_on_quit

    def _parse_arguments(self):
        """Parse command line arguments"""
        # create an argparse instance
        parser = argparse.ArgumentParser(prog="Initial Setup",
                                         description="Initial Setup is can run during the first start of a newly installed"
                                         "system to configure it according to the needs of the user.")
        parser.add_argument("--no-stdout-log", action="store_true", default=False, help="don't log to stdout")
        parser.add_argument("--no-multi-tty", action="store_true", default=False,
                            help="Don't run on multiple consoles.")
        parser.add_argument('--version', action='version', version=__version__)

        # parse arguments and return the result
        return parser.parse_args()

    def _load_kickstart(self):
        """Load the kickstart"""
        from pyanaconda import kickstart

        # Construct a commandMap with only the supported Anaconda's commands
        commandMap = dict((k, kickstart.commandMap[k]) for k in SUPPORTED_KICKSTART_COMMANDS)

        # Prepare new data object
        self.data = kickstart.AnacondaKSHandler(commandUpdates=commandMap)

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

        # if we got this far the kickstart should be valid, so send it to Boss as well
        boss = BOSS.get_proxy()
        report = KickstartReport.from_structure(
            boss.ReadKickstartFile(kickstart_path)
        )

        if not report.is_valid():
            message = "\n\n".join(map(str, report.error_messages))
            raise InitialSetupError(message)

        if self.external_reconfig:
            # set the reconfig flag in kickstart so that
            # relevant spokes show up
            services_proxy = SERVICES.get_proxy()
            services_proxy.SetSetupOnBoot(SETUP_ON_BOOT_RECONFIG)

        # Record if groups, users or root password has been set before Initial Setup
        # has been started, so that we don't trample over existing configuration.
        users_proxy = USERS.get_proxy()
        self._groups_already_configured = bool(users_proxy.Groups)
        self._users_already_configured = bool(users_proxy.Users)
        self._root_password_already_configured = users_proxy.IsRootPasswordSet

    def _setup_locale(self):
        log.debug("setting up locale")

        localization_proxy = LOCALIZATION.get_proxy()

        # Normalize the locale environment variables
        if localization_proxy.Kickstarted:
            locale_arg = localization_proxy.Language
        else:
            locale_arg = None
        setup_locale_environment(locale_arg, prefer_environment=True)
        setup_locale(os.environ['LANG'], text_mode=not self.gui_mode)

    def _initialize_network(self):
        log.debug("initializing network")
        network_proxy = NETWORK.get_proxy()
        network_proxy.CreateDeviceConfigurations()

    def _apply(self):
        # Do not execute sections that were part of the original
        # anaconda kickstart file (== have .seen flag set)

        log.info("applying changes")

        services_proxy = SERVICES.get_proxy()
        reconfig_mode = services_proxy.SetupOnBoot == SETUP_ON_BOOT_RECONFIG

        # data.selinux
        # data.firewall

        # Configure the timezone.
        timezone_proxy = TIMEZONE.get_proxy()
        for task_path in timezone_proxy.InstallWithTasks():
            task_proxy = TIMEZONE.get_proxy(task_path)
            sync_run_task(task_proxy)

        # Configure the localization.
        localization_proxy = LOCALIZATION.get_proxy()
        for task_path in localization_proxy.InstallWithTasks():
            task_proxy = LOCALIZATION.get_proxy(task_path)
            sync_run_task(task_proxy)

        # Configure persistent hostname
        network_proxy = NETWORK.get_proxy()
        network_task = network_proxy.ConfigureHostnameWithTask(True)
        task_proxy = NETWORK.get_proxy(network_task)
        sync_run_task(task_proxy)
        # Set current hostname
        network_proxy.SetCurrentHostname(network_proxy.Hostname)

        # Configure groups, users & root account
        #
        # NOTE: We only configure groups, users & root account if the respective
        #       kickstart commands are *not* seen in the input kickstart.
        #       This basically means that we will configure only what was
        #       set in the Initial Setup UI and will not attempt to configure
        #       anything that looks like it was configured previously in
        #       the Anaconda UI or installation kickstart.
        users_proxy = USERS.get_proxy()

        if self._groups_already_configured and not reconfig_mode:
            log.debug("skipping user group configuration - already configured")
        elif users_proxy.Groups:  # only run of there are some groups to create
            groups_task = users_proxy.ConfigureGroupsWithTask()
            task_proxy = USERS.get_proxy(groups_task)
            log.debug("configuring user groups via %s task", task_proxy.Name)
            sync_run_task(task_proxy)

        if self._users_already_configured and not reconfig_mode:
            log.debug("skipping user configuration - already configured")
        elif users_proxy.Users:  # only run if there are some users to create
            users_task = users_proxy.ConfigureUsersWithTask()
            task_proxy = USERS.get_proxy(users_task)
            log.debug("configuring users via %s task", task_proxy.Name)
            sync_run_task(task_proxy)

        if self._root_password_already_configured and not reconfig_mode:
            log.debug("skipping root password configuration - already configured")
        else:
            root_task = users_proxy.SetRootPasswordWithTask()
            task_proxy = USERS.get_proxy(root_task)
            log.debug("configuring root password via %s task", task_proxy.Name)
            sync_run_task(task_proxy)

        # Configure all addons
        log.info("executing addons")
        boss_proxy = BOSS.get_proxy()
        for service_name, object_path in boss_proxy.CollectInstallSystemTasks():
            task_proxy = DBus.get_proxy(service_name, object_path)
            sync_run_task(task_proxy)

        if self.external_reconfig:
            # prevent the reconfig flag from being written out
            # to kickstart if neither /etc/reconfigSys or /.unconfigured
            # are present
            services_proxy = SERVICES.get_proxy()
            services_proxy.SetSetupOnBoot(SETUP_ON_BOOT_DEFAULT)

        # Write the kickstart data to file
        log.info("writing the Initial Setup kickstart file %s", OUTPUT_KICKSTART_PATH)
        with open(OUTPUT_KICKSTART_PATH, "w") as f:
            f.write(str(self.data))
        log.info("finished writing the Initial Setup kickstart file")

        # Remove the reconfig files, if any - otherwise the reconfig mode
        # would start again next time the Initial Setup service is enabled.
        if self.external_reconfig:
            for reconfig_file in RECONFIG_FILES:
                if os.path.exists(reconfig_file):
                    log.debug("removing reconfig trigger file: %s" % reconfig_file)
                    os.remove(reconfig_file)

        # and we are done with applying changes
        log.info("all changes have been applied")

    def run(self):
        """Run Initial setup

        :param bool gui_mode: if GUI should be used (TUI is the default)

        :returns: True if the IS run was successful, False if it failed
        :rtype: bool
        """
        # also register boss shutdown & DBUS session cleanup via exit handler
        atexit.register(self._dbus_launcher.stop)

        # start dbus session (if not already running) and run boss in it
        try:
            self._dbus_launcher.start()
        except TimeoutError as e:
            log.error(str(e))
            return True

        self._load_kickstart()
        self._setup_locale()
        self._initialize_network()

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
            ui = initial_setup.gui.InitialSetupGraphicalUserInterface()
        else:
            # Import IS gui specifics
            import initial_setup.tui

            # Add addons to search paths
            initial_setup.tui.InitialSetupTextUserInterface.update_paths(self._addon_module_paths)

            # Initialize the UI
            log.debug("initializing TUI")
            ui = initial_setup.tui.InitialSetupTextUserInterface(self._args)

        # Pass the data object to user interface
        log.debug("setting up the UI")
        ui.setup(self.data)

        # Start the application
        log.info("starting the UI")
        ret = ui.run()

        # we need to reboot the machine if there is an EULA, that was not agreed
        if eula_available() and  not self.data.eula.agreed:
            log.warning("EULA has not been agreed - the system will be rebooted.")
            self._reboot_on_quit = True

        # TUI returns False if the app was ended prematurely
        # all other cases return True or None
        if ret is False:
            log.warning("ended prematurely in TUI")
            return True

        # apply changes
        self._apply()

        # in the TUI mode shutdown the multi TTY handler (if any)
        if not self.gui_mode and ui.multi_tty_handler:
            # TODO: wait for this to finish or make it blockng ?
            ui.multi_tty_handler.shutdown()

        # and we are done
        return True
