#############################################################################
# File		: rpmlint.spec
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Tue Sep 28 07:18:06 1999
# Version	: $Id$
# Purpose	: rules to create the rpmlint binary package.
#############################################################################
%define name rpmlint
%define version 0.15
%define release 1mdk

Summary: rpm correctness checker
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.bz2
URL: http://www.lepied.com/rpmlint/
Copyright: GPL
Group: Development/Other
BuildRoot: %{_tmppath}/%{name}-buildroot
Prefix: %{_prefix}
Requires: rpm-python, python >= 1.5.2, rpm-devel >= 3.0.3-35mdk, binutils, file, findutils, cpio, /lib/cpp, grep
BuildArchitectures: noarch
BuildRequires: python >= 1.5.2, rpm-devel >= 3.0.3-35mdk, make

%description
rpmlint is a tool to check common errors on rpm packages.
Binary and source packages can be checked.

%prep
%setup -q

%build
make

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,0755)
%doc COPYING ChangeLog INSTALL README*
%{prefix}/bin/*
%{prefix}/share/rpmlint
%config /etc/rpmlint/config

%changelog
* Tue Jun 27 2000 Frederic Lepied <flepied@mandrakesoft.com> 0.15-1mdk
- 0.15:
 o check non transparent pixmaps in icon path
 o added a check for soname
 o added a warning for packages that provide themselves (for Pixel)
 o corrected check for needs in menu files.
 o various exceptions added.

* Mon Apr 17 2000 Frederic Lepied <flepied@mandrakesoft.com> 0.14-1mdk
- 0.14:
 o MenuCheck: check old entries from KDE and GNOME and allow entries
for sections.
 o config: exceptions for urpmi, sash, octave, ghc, procmail, rsh.
 o extract temp files in <tmppath>/<pkgname>.<pid>

* Mon Apr 10 2000 Frederic Lepied <flepied@mandrakesoft.com> 0.13-1mdk
- 0.13:
 o MenuCheck: issue a warning if no icon specified (Chmouel).
              corrected list of correct sections (Chmouel).
 o FilesCheck: check ldconfig calls in %%post and %%postun if the package
provide a library.
 o config: new exceptions added.
 o BinariesCheck: check non sparc32 binaries in sparc packages.

* Fri Mar 31 2000 Frederic Lepied <flepied@mandrakesoft.com> 0.12-1mdk
- 0.12:
 o MenuCheck: check binaries launched by menus and
              check update-menus %%post and %%postun.
 o BinariesCheck: check for non sparc32 binaries in sparc rpms.

* Mon Mar 27 2000 Frederic Lepied <flepied@mandrakesoft.com> 0.11-1mdk
- 0.11:
 o check menu files.

* Tue Mar 14 2000 Frederic Lepied <flepied@mandrakesoft.com> 0.10-1mdk
- 1.10:
 o check .h, .a and .so in non devel package.
 o check files in /home.
 o corrected lists of groups.

* Mon Feb 28 2000 Frederic Lepied <flepied@mandrakesoft.com> 0.9.2-1mdk
- added a dependency on rpm-python.
- corrected rpm 3.0.4 support.

* Wed Feb 23 2000 Frederic Lepied <flepied@mandrakesoft.com> 0.9.1-1mdk
- updated to support the way rpm 3.0.4 stores file names.

* Thu Feb 10 2000 Frederic Lepied <flepied@mandrakesoft.com> 0.9-1mdk

- 0.9: * gpg support.
       * check release extension.
       * check non executable in bin directories.
       * new options: ValidGroups, ReleaseExtension and
	UseVersionInChangelog.

* Thu Dec 30 1999 Frederic Lepied <flepied@mandrakesoft.com> 0.8-1mdk

- 0.8: I18N checks, some exceptions added.

* Mon Nov 15 1999 Frederic Lepied <flepied@mandrakesoft.com>

- 0.7: more robust cleanup, filters are regexp now and added
exception for /var/catman subirs beeing setgid.

* Sat Oct 23 1999 Frederic Lepied <flepied@mandrakesoft.com>

- 0.6.1: corrected compilation step.

* Sat Oct 23 1999 Frederic Lepied <flepied@mandrakesoft.com>

- 0.6: filter output, documentation checks.

* Fri Oct 15 1999 Frederic Lepied <flepied@mandrakesoft.com>

- 0.5: FHS check, configuration files.

* Fri Oct  8 1999 Chmouel Boudjnah <chmouel@mandrakesoft.com>
- Add Doc.

* Thu Oct  7 1999 Frederic Lepied <flepied@mandrakesoft.com>

- version 0.4: pgp check and group name check.

* Wed Oct  6 1999 Frederic Lepied <flepied@mandrakesoft.com>

- version 0.3.

* Mon Oct  4 1999 Frederic Lepied <flepied@mandrakesoft.com>

- version 0.2.

* Fri Oct  1 1999 Frederic Lepied <flepied@mandrakesoft.com>

- First spec file for Mandrake distribution.

# rpmlint.spec ends here
