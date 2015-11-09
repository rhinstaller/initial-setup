Summary: Initial system configuration utility
Name: initial-setup
URL: http://fedoraproject.org/wiki/InitialSetup
Version: 0.3.9.30
Release: 1%{?dist}

# This is a Red Hat maintained package which is specific to
# our distribution.
#
# The source is thus available only from within this SRPM
# or via direct git checkout:
# git clone git://git.fedorahosted.org/initial-setup.git
Source0: %{name}-%{version}.tar.gz

%define debug_package %{nil}
%define anacondaver 21.48.22.36

License: GPLv2+
Group: System Environment/Base
BuildRequires: gettext
BuildRequires: python2-devel
BuildRequires: python-setuptools
BuildRequires: python-nose
BuildRequires: systemd-units
BuildRequires: gtk3-devel
BuildRequires: gtk-doc
BuildRequires: gobject-introspection-devel
BuildRequires: glade-devel
BuildRequires: pygobject3
BuildRequires: python-di

Requires: python
Requires: anaconda-tui >= %{anacondaver}
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
Requires: libreport-python
Requires: python-di
Conflicts: firstboot < 19.2

%description
The initial-setup utility runs after installation.  It guides the user through
a series of steps that allows for easier configuration of the machine.

%package gui
Summary: Graphical user interface for the initial-setup utility
Requires: gtk3
Requires: anaconda-gui >= %{anacondaver}
Requires: %{name} = %{version}-%{release}
Requires: firstboot(windowmanager)

%description gui
The initial-setup-gui package contains a graphical user interface for the
initial-setup utility.

%prep
%setup -q

# remove upstream egg-info
rm -rf *.egg-info

%build
%{__python} setup.py build
make po-files

%check

%install
%{__python} setup.py install --skip-build --root $RPM_BUILD_ROOT
make install-po-files
%find_lang %{name}

%post
%systemd_post initial-setup-text.service
%systemd_post initial-setup.service

%preun
%systemd_preun initial-setup-text.service
%systemd_preun initial-setup.service

%postun
%systemd_postun initial-setup-text.service
%systemd_postun initial-setup.service

%post gui
%systemd_post initial-setup-graphical.service

%preun gui
%systemd_preun initial-setup-graphical.service

%postun gui
%systemd_postun initial-setup-graphical.service

%files -f %{name}.lang
%doc COPYING README
%{python_sitelib}/initial_setup*
%exclude %{python_sitelib}/initial_setup/gui
%{_unitdir}/initial-setup-text.service
%{_unitdir}/initial-setup.service
%{_libexecdir}/%{name}/run-initial-setup
%{_libexecdir}/%{name}/firstboot-windowmanager
%{_libexecdir}/%{name}/initial-setup-text
%{_libexecdir}/%{name}/text-service-is-deprecated

%ifarch s390 s390x
%{_sysconfdir}/profile.d/initial-setup.sh
%{_sysconfdir}/profile.d/initial-setup.csh
%endif

%files gui
%{python_sitelib}/initial_setup/gui/*
%{_unitdir}/initial-setup-graphical.service
%{_libexecdir}/%{name}/initial-setup-graphical
%{_libexecdir}/%{name}/graphical-service-is-deprecated


%changelog
* Tue Sep 22 2015 Martin Kolman <mkolman@redhat.com> - 0.3.9.30-1
- Only root should be able to read the initial-setup-ks.cfg file (#1264336) (mkolman)
  Resolves: rhbz#1264336

* Tue Sep 01 2015 Martin Kolman <mkolman@redhat.com> - 0.3.9.29-1
- Move gui scriptlets to the gui subpackage (#1181209) (mkolman)
  Resolves: rhbz#1181209

* Thu Aug 27 2015 Martin Kolman <mkolman@redhat.com> - 0.3.9.28-1
- Run the TUI service before hvc0.service (#1209731) (mmatsuya)
  Resolves: rhbz#1209731
- Don't create /etc/sysconfig/initial-setup on s390 (#1181209) (mkolman)
  Related: rhbz#1181209
- Setup the locale before starting the UI (dshea)
  Resolves: rhbz#1198642

* Wed Jul 22 2015 Martin Kolman <mkolman@redhat.com> - 0.3.9.27-1
- Switch to Zanata for translations (#1229747) (mkolman)
  Related: rhbz#1229747

* Mon Jul 13 2015 Martin Kolman <mkolman@redhat.com> - 0.3.9.26-2
- Don't try to run nonexistent tests (#1229747) (mkolman)
  Related: rhbz#1229747

* Thu Jul 9 2015 Martin Kolman <mkolman@redhat.com> - 0.3.9.26-1
- Use systemd service status for run detection on the S390 console (#1181209) (mkolman)
  Resolves: rhbz#1181209
- Bump the required Anaconda version (#1229747) (mkolman)
  Related: rhbz#1229747

* Fri Jul 3 2015 Martin Kolman <mkolman@redhat.com> - 0.3.9.25-2
- Don't show the EULA spoke in reconfig mode if license is already accepted (#1110439) (mkolman)
  Related: rhbz#1110439
- Read the kickstart from previous IS run, if available (#1110439) (mkolman)
  Related: rhbz#1110439
- Add support for externally triggered reconfig mode (#1110439) (mkolman)
  Resolves: rhbz#1110439

* Wed Jun 17 2015 Martin Kolman <mkolman@redhat.com> - 0.3.9.24-1
- Make Initial Setup compatible with rebased Anaconda (#1229747) (mkolman)
  Resolves: rhbz#1229747
- Log the reason if GUI import fails (#1229747) (mkolman)
  Related: rhbz#1229747

* Tue Jan 20 2015 Martin Kolman <mkolman@redhat.com> - 0.3.9.23-1
- Redirect the EULA spoke help button to the Initial Setup hub help file (#1072033) (mkolman)
  Related: rhbz#1072033

* Fri Jan 9 2015 Martin Kolman <mkolman@redhat.com> - 0.3.9.22-1
- Fixes for profile.d scripts (#1180576) (jstodola)
  Resolves: rhbz#1180576

* Fri Nov 21 2014 Martin Kolman <mkolman@redhat.com> - 0.3.9.21-1
- Move the firstboot(windowmanager) dependency to the GUI package (#999464) (mkolman)
  Related: rhbz#999464

* Mon Nov 3 2014 Martin Kolman <mkolman@redhat.com> - 0.3.9.20-1
- Explicitly require the main package in the GUI sub package (#1078917) (mkolman)
  Related: #1078917

* Thu Oct 23 2014 Martin Kolman <mkolman@redhat.com> - 0.3.9.19-1
- Point to the new Initial Setup wiki page (#1154656) (mkolman)
  Resolves: rhbz#1154656
- Add syslog logging support (#1153768) (mkolman)
  resolves: rhbz#1153768

* Fri Oct 3 2014 Martin Kolman <mkolman@redhat.com> - 0.3.9.18-1
- Fix Initial Setup to correctly support the Anaconda built-in Help (#1072033) (mkolman)
  Related: rhbz#1072033

* Thu Oct 2 2014 Martin Kolman <mkolman@redhat.com> - 0.3.9.17-1
- Fix register_event_cb function signature (#1072033) (mkolman)
  Related: rhbz#1072033

* Mon Sep 29 2014 Martin Kolman <mkolman@redhat.com> - 0.3.9.16-1
- Populate README (#1110178) (mkolman)
  Resolves: rhbz#1110178

* Tue Sep 16 2014 Martin Kolman <mkolman@redhat.com> - 0.3.9.15-1
- Remove the modules folder (#999464) (mkolman)
  Related: rhbz#999464

* Thu Sep 11 2014 Martin Kolman <mkolman@redhat.com> - 0.3.9.14-1
- Bump Anaconda version requirement for the GUI split (mkolman)
  Related: rhbz#999464
- Split GUI code into a separate package (#999464) (vpodzime)
  Resolves: rhbz#999464

* Mon Sep 8 2014 Martin Kolman <mkolman@redhat.com> - 0.3.9.13-1
- Use the Licensing category for the EULA (#1039677) (mkolman)
  Resolves: rhbz#1039677

* Tue Apr 1 2014 Martin Kolman <mkolman@redhat.com> - 0.3.9.12-1
- Set initial-setup translation domain for the hub and EULA spoke (mkolman)
  Resolves: rhbz#1040240

* Tue Mar 18 2014 Martin Kolman <mkolman@redhat.com> - 0.3.9.11-1
- Rebuild with new translations
  Resolves: rhbz#1040240

* Mon Feb 24 2014 Martin Kolman <mkolman@redhat.com> - 0.3.9.10-1
- Rebuild with new translations
  Resolves: rhbz#1040240

* Tue Feb 11 2014 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.9.9-1
- Try to quit plymouth before running our X server instance
  Resolves: rhbz#1058329
- Get rid of the empty debuginfo package
  Related: rhbz#1057590

* Fri Jan 25 2014 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.9.8-1
- Ignore the SIGINT
  Resolves: rhbz#1035590

* Fri Jan 24 2014 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.9.7-2
- Make initial-setup an arch specific package
  Resolves: rhbz#1057590

* Thu Jan 23 2014 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.9.7-1
- Include new translations
  Resolves: rhbz#1030361

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 0.3.9.6-2
- Mass rebuild 2013-12-27

* Wed Dec 18 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.9.6-1
- Ignore .po and generated files in po/ (dshea)
  Related: rhbz#1040240
- Mark title strings in the initial-setup hub as translatable (dshea)
  Resolves: rhbz#1040240
- Reword the EULA spokes' status messages (vpodzime)
  Resolves: rhbz#1039672
- Cancel formatting of EULA when putting it into the text buffer (vpodzime)
  Resolves: rhbz#1039675

* Mon Nov 18 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.9.5-1
- Override distribution text in spokes (vpodzime)
  Resolves: rhbz#1028370

* Fri Nov 08 2013 David Cantrell <dcantrell@redhat.com> - 0.3.9.4-2
- EULA is now in /usr/share/redhat-release/EULA
  Resolves: rhbz#1028365

* Fri Nov 01 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.9.4-1
- Read licence files as utf-8 encoded (vpodzime)
  Resolves: rhbz#1023052
- Inform user that the system may be rebooted (vpodzime)
  Resolves: rhbz#1022040

* Mon Oct 14 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.9.3-1
- Fix how spokes are collected for the I-S main hub
  Related: rhbz#1000409
- Add TUI Eula spoke
  Related: rhbz#1000409
- Reboot the system if EULA is not agreed
  Related: rhbz#1000409

* Tue Oct 08 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.9.2-1
- Put license view into a scrolled window (#1015005) (vpodzime)
- Clear the default text before inserting the EULA (dshea)
  Related: rhbz#1015005

* Thu Sep 26 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.9.1-1
- Yet another serial console in ARMs (vpodzime)
  Related: rhbz#1000409
- Fix the base mask of initial_setup gui submodules (vpodzime)
  Related: rhbz#1000409
- Specify and use environment of the main hub (vpodzime)
  Related: rhbz#1000409
- EULA agreement spoke (#1000409) (vpodzime)
- Require new version of anaconda with eula command support (vpodzime)
  Related: rhbz#1000409

* Wed Sep 11 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.8-1
- Read /etc/os-release to get product title (#1000426) (vpodzime)
- Don't let product_title() return None (vpodzime)
- Apply the timezone and NTP configuration (#985566) (hdegoede)
- Make handling translations easier (vpodzime)
- Make translations work (vpodzime)
- Prevent getty on various services killing us (#979174) (vpodzime)
- Initialize network logging for the network spoke (vpodzime)

* Mon Aug 12 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.6-4
- Require a new version of the anaconda with fixed dependencies.

* Fri Jul 26 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.6-3
- Rebuild with dependencies available in RHEL tree.

* Tue Jun 18 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.6-2
- Rebuild with dependencies available.

* Tue Jun 18 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.6-1
- Make serial-getty wait for us as well (#970719) (vpodzime)
- Disable the service only on successful exit (#967617) (vpodzime)

* Mon May 22 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.5-1
- Reference the new repository in the .spec file (vpodzime)
- Prevent systemd services from running on live images (#962196) (awilliam)
- Don't traceback if the expected kickstart file doesn't exist (#950796) (vpodzime)

* Mon Apr 8 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.4-3
- Rebuild with fixed spec that partly reverts the previous change

* Fri Apr 5 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.4-2
- Rebuild with fixed spec that enables services after installation

* Thu Mar 28 2013 Martin Sivak <msivak@euryale.brq.redhat.com> - 0.3.4-1
- Search for proper UI variant of addons
- Add addon directories to sys.path

* Tue Mar 26 2013 Martin Sivak <msivak@euryale.brq.redhat.com> - 0.3.3-1
- Systemd unit files improved

* Tue Mar 26 2013 Martin Sivak <msivak@euryale.brq.redhat.com> - 0.3.2-1
- Modify the ROOT_PATH properly
- Do not execute old ksdata (from anaconda's ks file)
- Save the resulting configuration to /root/initial-setup-ks.cfg

* Tue Mar 26 2013 Martin Sivak <msivak@euryale.brq.redhat.com> - 0.3.1-2
- Require python-di package

* Thu Mar 21 2013 Martin Sivak <msivak@euryale.brq.redhat.com> - 0.3.1-1
- Use updated Anaconda API
- Request firstboot environment spokes
- Initialize anaconda threading properly

* Wed Mar 13 2013 Martin Sivak <msivak@euryale.brq.redhat.com> - 0.3-1
- Use updated Anaconda API
- Fix systemd units
- Add localization spokes to TUI
- Write changes to disk
- Conflict with old firstboot

* Tue Feb 13 2013 Martin Sivak <msivak@redhat.com> 0.2-1
- Updates for package review
- Firstboot-windowmanager script

* Tue Feb 13 2013 Martin Sivak <msivak@redhat.com> 0.1-3
- Updates for package review

* Tue Jan 22 2013 Martin Sivak <msivak@redhat.com> 0.1-2
- Updates for package review

* Tue Nov 06 2012 Martin Sivak <msivak@redhat.com> 0.1-1
- Initial release
