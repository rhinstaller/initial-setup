%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}

Summary: Initial system configuration utility
Name: firstboot2
URL: http://fedoraproject.org/wiki/FirstBoot
Version: 19.0
Release: 1%{?dist}
# This is a Red Hat maintained package which is specific to
# our distribution.  Thus the source is only available from
# within this srpm.
Source0: %{name}-%{version}.tar.gz

License: GPLv2+
Group: System Environment/Base
ExclusiveOS: Linux
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: gettext
BuildRequires: python-devel, python-setuptools-devel
BuildRequires: systemd-units
Requires: gtk3, python, python-gi
Requires: anaconda
Requires(post): systemd-units systemd-sysv chkconfig
Requires(preun): systemd-units
Requires(postun): systemd-units
Requires: firstboot(windowmanager)
Requires: libreport-python

%define debug_package %{nil}

%description
The firstboot utility runs after installation.  It guides the user through
a series of steps that allows for easier configuration of the machine.

%prep
%setup -q

%build
%{__python} setup.py build

%install
%{__python} setup.py --skip-build install
%find_lang %{name}

%clean
rm -rf %{buildroot}

%post
if [ $1 -ne 2 -a ! -f /etc/sysconfig/firstboot ]; then
  platform="$(arch)"
  if [ "$platform" = "s390" -o "$platform" = "s390x" ]; then
    echo "RUN_FIRSTBOOT=YES" > /etc/sysconfig/firstboot
  else
    %systemd_post firstboot-graphical.service
  fi
fi

%preun
if [ $1 = 0 ]; then
  rm -rf /usr/share/firstboot2/*.pyc
  rm -rf /usr/share/firstboot2/modules/*.pyc
fi
%systemd_preun firstboot-graphical.service

%postun
%systemd_postun_with_restart firstboot-graphical.service

%files -f %{name}.lang
%defattr(-,root,root,-)
%dir %{_datadir}/firstboot/
%dir %{_datadir}/firstboot/modules/
%dir %{_datadir}/firstboot/themes/
%dir %{_datadir}/firstboot/themes/default
%{python_sitelib}/*
%{_sbindir}/firstboot
%{_datadir}/firstboot/modules/create_user.py*
%{_datadir}/firstboot/modules/date.py*
%{_datadir}/firstboot/modules/eula.py*
%{_datadir}/firstboot/modules/welcome.py*
%{_datadir}/firstboot/themes/default/*
/lib/systemd/system/firstboot-graphical.service
%ifarch s390 s390x
%dir %{_sysconfdir}/profile.d
%{_sysconfdir}/profile.d/firstboot.sh
%{_sysconfdir}/profile.d/firstboot.csh
%endif


%changelog
* Tue Nov 06 2012 Martin Sivak <msivak@redhat.com> 19.0-1
- Inital release
