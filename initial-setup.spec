Summary: Initial system configuration utility
Name: initial-setup
URL: http://fedoraproject.org/wiki/FirstBoot
Version: 0.3.9.5
Release: 1%{?dist}
BuildArch: noarch

# This is a Red Hat maintained package which is specific to
# our distribution.
#
# The source is thus available only from within this SRPM
# or via direct git checkout:
# git clone git://git.fedorahosted.org/initial-setup.git
Source0: %{name}-%{version}.tar.gz

%define anacondaver 19.31.27

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
BuildRequires: anaconda >= %{anacondaver}
BuildRequires: python-di
Requires: gtk3
Requires: python
Requires: anaconda >= %{anacondaver}
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
Requires: firstboot(windowmanager)
Requires: libreport-python
Requires: python-di
Conflicts: firstboot < 19.2

%description
The initial-setup utility runs after installation.  It guides the user through
a series of steps that allows for easier configuration of the machine.

%prep
%setup -q

# remove upstream egg-info
rm -rf *.egg-info

%build
%{__python} setup.py build
make po-files

%check
%{__python} setup.py nosetests

%install
%{__python} setup.py install --skip-build --root $RPM_BUILD_ROOT
make install-po-files
%find_lang %{name}

%post
if [ $1 -ne 2 -a ! -f /etc/sysconfig/initial-setup ]; then
  platform="$(arch)"
  if [ "$platform" = "s390" -o "$platform" = "s390x" ]; then
    echo "RUN_INITIAL_SETUP=YES" > /etc/sysconfig/initial-setup
  else
    %systemd_post initial-setup-graphical.service
    %systemd_post initial-setup-text.service
  fi
fi

%preun
%systemd_preun initial-setup-graphical.service
%systemd_preun initial-setup-text.service

%postun
%systemd_postun_with_restart initial-setup-graphical.service
%systemd_postun_with_restart initial-setup-text.service

%files -f %{name}.lang
%doc COPYING README
%dir %{_datadir}/initial-setup/
%dir %{_datadir}/initial-setup/modules/
%{python_sitelib}/*
%{_bindir}/initial-setup
%{_bindir}/firstboot-windowmanager
%{_datadir}/initial-setup/modules/*

%{_unitdir}/initial-setup-graphical.service
%{_unitdir}/initial-setup-text.service

%ifarch s390 s390x
%{_sysconfdir}/profile.d/initial-setup.sh
%{_sysconfdir}/profile.d/initial-setup.csh
%endif


%changelog
* Mon Nov 18 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.9.5-1
- Override distribution text in spokes (#1028370) (vpodzime)

* Fri Nov 01 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.9.4-1
- Read licence files as utf-8 encoded (#1023052) (vpodzime)
- Inform user that the system may be rebooted (#1022040) (vpodzime)

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

* Tue Sep 10 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.8-1
- Read /etc/os-release to get product title (#1000426) (vpodzime)
- Don't let product_title() return None (vpodzime)
- Apply the timezone and NTP configuration (#985566) (hdegoede)
- Make handling translations easier (vpodzime)
- Make translations work (vpodzime)
- Sync changelog with downstream (vpodzime)

* Tue Aug 27 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.7-1
- Prevent getty on various services killing us (#979174) (vpodzime)
- Initialize network logging for the network spoke (vpodzime)

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.3.6-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

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
