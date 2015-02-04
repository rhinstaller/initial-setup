Initial Setup
=============
Initial Setup is an application that can run during the first start
of a newly installed computer and makes it possible to configure the
computer according to the needs of the user.

As most of the configuration options are already present during the
OS installation in Anaconda, Initial Setup mainly hosts options that
need to be presented during the first start, such as displaying the
EULA on RHEL. Initial Setup is also often used to create a user account,
as many systems are often automatically installed with kickstart
and the user is only expected to create their own user account once
the newly installed machine is started for the first time.

Still, while Initial Setup normally does not have many options
available, if the firstboot --reconfig kickstart command is provided
in the installation kickstart, Initial Setup will show all configuration
options available. This is usually used for OEM OS installations,
where an OEM installs the computer, which is then shipped to the end user
which uses Initial Setup for the final configuration of the operating system.

Architecture
============
Initial Setup is basically just a thin wrapper for running spokes from Anaconda.
Still, it has its own Hub, one spoke (the EULA spoke) and a translation domain ("initial-setup").

As with Anaconda, Initial Setup has both a GUI and TUI version and the package is split
into a core and GUI & TUI sub packages.

As Initial Setup needs to run during the early boot, it is started by a systemd unit
configured to start before the normal login screen. On RHEL7 Initial Setup is by default
followed by the legacy Firstboot utility, which hosts the Subscription Manager plugin.
If the given OS instance uses the Gnome 3 desktop environment, Firstboot is followed by
the Gnome Initial Setup, which enables the user to customize their computer even more.
On Fedora Initial Setup is followed directly by GIS, provided Gnome 3 is installed.

* RHEL7: IS -> Firstboot -> [GIS]
* Fedora: IS -> [GIS]

Addons
======
Like Anaconda, also Initial Setup can be used to host third party addons - flexible
yet powerful modules that can configure the system based on data in kickstart
while presenting a nice UI to the user. Addons can have a GUI, TUI or can be
headless, working only with data in their kickstart section or from other sources.

For comprehensive documentation about Anaconda/Intial Setup see the
"Anaconda Addon Development Guide" by Vratislav Podzimek:

* https://vpodzime.fedorapeople.org/anaconda-addon-development-guide/

Contributing
============
* Initial Setup is released under GPLv2+
* upstream source code repository is on GitHub: https://github.com/rhinstaller/initial-setup
* for patch review Initial Setup uses the Anaconda Patches mailing list: https://lists.fedorahosted.org/mailman/listinfo/anaconda-patches
  (please note that you need to be subscribed to the list to send patches, due to previous issues with SPAM on the list)
