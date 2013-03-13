Summary: Initial system configuration utility
Name: initial-setup
URL: http://fedoraproject.org/wiki/FirstBoot
Version: 0.3
Release: 1%{?dist}
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
BuildRequires: anaconda >= 19.11
Requires: gtk3
Requires: python
Requires: anaconda >= 19.11
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units
Requires: firstboot(windowmanager)
Requires: libreport-python
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

# Check is disabled until Gtk bug rhbz#902401 is resolved
#%check
#%{__python} setup.py nosetests

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
