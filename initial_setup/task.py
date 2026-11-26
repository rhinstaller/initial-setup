import logging

from pyanaconda.core.constants import SETUP_ON_BOOT_RECONFIG, SETUP_ON_BOOT_DEFAULT
from pyanaconda.core.dbus import DBus
from pyanaconda.installation_tasks import TaskQueue, DBusTask
from pyanaconda.modules.common.constants.services import SERVICES, TIMEZONE, LOCALIZATION, NETWORK, USERS, BOSS
from pyanaconda.modules.common.task import Task, sync_run_task
from pyanaconda.core.i18n import _

log = logging.getLogger("initial-setup")


class InitialSetupTask(Task):
    def __init__(self,
                 groups_already_configured=False,
                 users_already_configured=False,
                 root_password_already_configured=False):
        super().__init__()
        self._total_steps = 0
        self._groups_already_configured = groups_already_configured
        self._users_already_configured = users_already_configured
        self._root_password_already_configured = root_password_already_configured

    @property
    def name(self):
        """Name of the task"""
        return "Run the initial setup queue."

    @property
    def steps(self):
        """Total number of steps."""
        return self._total_steps

    def _queue_started_cb(self, task):
        """The installation queue was started."""
        self.report_progress(task.status_message)

    def _task_completed_cb(self, task):
        """The installation task was completed."""
        self.report_progress("", step_size=1)

    def _task_started_cb(self, task):
        """The installation task was completed."""
        self.report_progress(task.name)

    def _progress_report_cb(self, step, message):
        """Handle a progress report of a task."""
        self.report_progress(message)

    def run(self):
        """Run the task."""
        log.info("applying changes")

        queue = TaskQueue("Initial Setup")

        # connect progress reporting
        queue.queue_started.connect(self._queue_started_cb)
        queue.task_completed.connect(self._task_completed_cb)
        queue.task_started.connect(self._task_started_cb)

        services_proxy = SERVICES.get_proxy()
        reconfig_mode = services_proxy.SetupOnBoot == SETUP_ON_BOOT_RECONFIG

        # data.selinux
        # data.firewall

        # Configure the timezone.
        timezone_proxy = TIMEZONE.get_proxy()
        for task_path in timezone_proxy.InstallWithTasks():
            task_proxy = TIMEZONE.get_proxy(task_path)
            queue.append(DBusTask(task_proxy))

        # Configure the localization.
        localization_proxy = LOCALIZATION.get_proxy()
        for task_path in localization_proxy.InstallWithTasks():
            task_proxy = LOCALIZATION.get_proxy(task_path)
            queue.append(DBusTask(task_proxy))

        # Configure persistent hostname
        network_proxy = NETWORK.get_proxy()
        network_task = network_proxy.ConfigureHostnameWithTask(True)
        task_proxy = NETWORK.get_proxy(network_task)
        queue.append(DBusTask(task_proxy))
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
            queue.append(DBusTask(task_proxy))

        if self._users_already_configured and not reconfig_mode:
            log.debug("skipping user configuration - already configured")
        elif users_proxy.Users:  # only run if there are some users to create
            users_task = users_proxy.ConfigureUsersWithTask()
            task_proxy = USERS.get_proxy(users_task)
            log.debug("configuring users via %s task", task_proxy.Name)
            queue.append(DBusTask(task_proxy))

        if self._root_password_already_configured and not reconfig_mode:
            log.debug("skipping root password configuration - already configured")
        else:
            root_task = users_proxy.SetRootPasswordWithTask()
            task_proxy = USERS.get_proxy(root_task)
            log.debug("configuring root password via %s task", task_proxy.Name)
            queue.append(DBusTask(task_proxy))

        # Configure all addons
        log.info("executing addons")
        boss_proxy = BOSS.get_proxy()
        for service_name, object_path in boss_proxy.CollectInstallSystemTasks():
            task_proxy = DBus.get_proxy(service_name, object_path)
            queue.append(DBusTask(task_proxy))

        for item in queue.nested_items:
            if isinstance(item, DBusTask):
                item._progress_cb = self._progress_report_cb

        self._total_steps = queue.task_count

        # log contents of the main task queue
        log.info(queue.summary)

        # start the task queue
        queue.start()

        # done
        self.report_progress(_("Complete!"), step_number=self.steps)
