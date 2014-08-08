Summary: Initial system configuration utility
Name: initial-setup
URL: http://fedoraproject.org/wiki/FirstBoot
Version: 0.3.23
Release: 1%{?dist}

# This is a Red Hat maintained package which is specific to
# our distribution.
#
# The source is thus available only from within this SRPM
# or via direct git checkout:
# git clone git://git.fedorahosted.org/initial-setup.git
Source0: %{name}-%{version}.tar.gz

%define debug_package %{nil}
%define anacondaver 21.46

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

Requires: python
Requires: anaconda-tui >= %{anacondaver}
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
Requires: libreport-python
Requires: python-di
Requires: util-linux
Conflicts: firstboot < 19.2

%description
The initial-setup utility runs after installation.  It guides the user through
a series of steps that allows for easier configuration of the machine.

%package gui
Summary: Graphical user interface for the initial-setup utility
Requires: gtk3
Requires: anaconda-gui >= %{anacondaver}
Requires: firstboot(windowmanager)
Requires: initial-setup

%description gui
The initial-setup-gui package contains a graphical user interface for the
initial-setup utility.

%prep
%setup -q

# remove upstream egg-info
rm -rf *.egg-info

%build
python setup.py build
make po-files

%check
export XDG_RUNTIME_DIR=/tmp
python setup.py nosetests

%install
python setup.py install --skip-build --root $RPM_BUILD_ROOT
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
%{python_sitelib}/initial_setup*
%exclude %{python_sitelib}/initial_setup/gui
%{_bindir}/initial-setup
%{_bindir}/firstboot-windowmanager
%{_unitdir}/initial-setup-text.service

%ifarch s390 s390x
%{_sysconfdir}/profile.d/initial-setup.sh
%{_sysconfdir}/profile.d/initial-setup.csh
%endif

%files gui
%{python_sitelib}/initial_setup/gui/*
%{_unitdir}/initial-setup-graphical.service

%post gui
if [ $1 -ne 2 -a ! -f /etc/sysconfig/initial-setup ]; then
  platform="$(arch)"
  if [ "$platform" = "s390" -o "$platform" = "s390x" ]; then
    echo "RUN_INITIAL_SETUP=YES" > /etc/sysconfig/initial-setup
  else
    %systemd_post initial-setup-graphical.service
  fi
fi

%preun gui
%systemd_preun initial-setup-graphical.service

%postun gui
%systemd_postun_with_restart initial-setup-graphical.service

%changelog
* Fri Aug 08 2014 Martin Kolman <mkolman@redhat.com> - 0.3.23-1
- Adapt to class changes in Anaconda (vpodzime)

* Fri Jul 04 2014 Martin Kolman <mkolman@redhat.com> - 0.3.22-1
- Update the initial-setup hub for the new HubWindow API (dshea)

* Sat May 31 2014 Peter Robinson <pbrobinson@fedoraproject.org> 0.3.21-2
- Only the GUI needs a window manager

* Wed May 28 2014 Martin Kolman <mkolman@redhat.com> - 0.3.21-1
- Adapt to python-nose API change (mkolman)

* Thu May 22 2014 Martin Kolman <mkolman@redhat.com> - 0.3.20-1
- Adapt Initial Setup to the new way Anaconda handles root path (#1099581) (vpodzime)

* Tue May 06 2014 Martin Kolman <mkolman@redhat.com> - 0.3.19-1
- Bump required Anaconda version due to TUI category handling change (mkolman)
- Override Hub collect methods also in TUI hub (mkolman)
- Translation update

* Mon Apr 28 2014 Martin Kolman <mkolman@redhat.com> - 0.3.18-1
- Remove debugging code that was left in the tarball by mistake (#1091470) (mkolman)
- Translation update

* Fri Apr 11 2014 Martin Kolman <mkolman@redhat.com> - 0.3.17-1
- Set initial-setup translation domain for the hub (#1040240) (mkolman)

* Thu Apr 03 2014 Martin Kolman <mkolman@redhat.com> - 0.3.16-1
- initial-setup-gui requires the initial-setup package (vpodzime)

* Wed Mar 19 2014 Martin Kolman <mkolman@redhat.com> - 0.3.15-1
- Import the product module (#1077390) (vpodzime)

* Tue Feb 11 2014 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.14-1
- Try to quit plymouth before running our X server instance (#1058329)
- Get rid of the empty debuginfo package (#1062738)

* Wed Feb 05 2014 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.13-1
- Make Initial Setup an arch specific package (#1057590) (vpodzime)

* Thu Nov 28 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.12-1
- Adapt to changes in anaconda tui spoke categories (#1035462) (vpodzime)
- Ignore the SIGINT (#1035590) (vpodzime)

* Wed Nov 20 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.11-1
- Fix how spokes are collected for the I-S main hub (vpodzime)
- Override distribution text in spokes (#1028370) (vpodzime)
- Get rid of the useless modules directory (vpodzime)
- Split GUI code into a separate package (#999464) (vpodzime)
- Fallback to text UI if GUI is not available (vpodzime)

* Tue Nov 05 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.10-1
- Do not try to kill unexisting process (vpodzime)
- Add some logging to our shell scripts (vpodzime)

* Thu Sep 26 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.9-1
- Yet another serial console in ARMs (#1007163) (vpodzime)
- Fix the base mask of initial_setup gui submodules (vpodzime)
- Specify and use environment of the main hub (vpodzime)

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

* Wed May 22 2013 Vratislav Podzimek <vpodzime@redhat.com> - 0.3.5-1
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

* Wed Feb 13 2013 Martin Sivak <msivak@redhat.com> 0.2-1
- Updates for package review
- Firstboot-windowmanager script

* Wed Feb 13 2013 Martin Sivak <msivak@redhat.com> 0.1-3
- Updates for package review

* Tue Jan 22 2013 Martin Sivak <msivak@redhat.com> 0.1-2
- Updates for package review

* Tue Nov 06 2012 Martin Sivak <msivak@redhat.com> 0.1-1
- Initial release
