Summary: Initial system configuration utility
Name: initial-setup
URL: http://fedoraproject.org/wiki/FirstBoot
Version: 0.3.4
Release: 3%{?dist}
BuildArch: noarch

# This is a Red Hat maintained package which is specific to
# our distribution.
#
# The source is thus available only from within this SRPM
# or via direct git checkout:
# git clone git://fedorapeople.org/home/fedora/msivak/public_git/firstboot2.git
Source0: %{name}-%{version}.tar.gz

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
BuildRequires: python-babel
BuildRequires: anaconda >= 19.13
BuildRequires: python-di
Requires: gtk3
Requires: python
Requires: anaconda >= 19.13
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
%{__python} setup.py compile_catalog -D %{name} -d locale

%check
%{__python} setup.py nosetests

%install
%{__python} setup.py install --skip-build --root $RPM_BUILD_ROOT
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
