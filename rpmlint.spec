#############################################################################
# File		: rpmlint.spec
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Tue Sep 28 07:18:06 1999
# Version	: $Id$
# Purpose	: rules to create the rpmlint binary package.
#############################################################################
%define name rpmlint
%define version 0.26
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
Requires: rpm-python, python >= 1.5.2, rpm-devel >= 3.0.3-35mdk, binutils, file, findutils, cpio, /lib/cpp, grep, /bin/bash
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
%config(noreplace) /etc/rpmlint/config

%changelog
* Fri Nov 10 2000 Frederic Lepied <flepied@mandrakesoft.com> 0.26-1mdk

- Config.py: added various exceptions.

- TagsCheck.py: o allow multiple licenses.
                o don't report anymore the package-provides-itself warning because
                it's the default in rpm 4.
                o try to not report incoherent-version-in-changelog for sub-packages.

- MenuCheck.py: correct the non-transparent-xpm check.

- FilesCheck.py: don't report buggy length-symlink anymore.

* Thu Oct 12 2000 Frederic Lepied <flepied@mandrakesoft.com> 0.25-1mdk

- Config.py: added exception for sympa, rpm and bcast.

- TagsCheck.py: o check that devel package depends on the base
                  package with the same version.
                o check that summary begins with a

- PostCheck.py: o check dangerous commands.
                ocheck reference to ~ or $HOME.

- MenuCheck.py: o check that titles and longtitles begin by a capital
                  letter.
                o check that no version is included in title and longtitle.
                o /lib/cpp errors to /dev/null for new cpp.

- FilesCheck.py: check package owning system dirs.

- SpecCheck.py: o new check.
                o check name of spec file.
                o check use of $RPM_SOURCE_DIR.
                o warn if a patch is not applied.

* Mon Oct  2 2000 Frederic Lepied <flepied@mandrakesoft.com> 0.24-1mdk
- FilesCheck.py: added apache and postgres to standard groups.
- TagsCheck.py: spell check a la Debian.

* Fri Sep 29 2000 Frederic Lepied <flepied@mandrakesoft.com> 0.23-1mdk
- MenuCheck.py: added Applications/Accessibility.
                check that menu	files are readable by everyone.
- Config.py: removed exception for /home.
             added exceptions for vixie-cron.
- FilesCheck.py: check cvs internal files.

* Tue Sep 12 2000 Frederic Lepied <flepied@mandrakesoft.com> 0.22-1mdk
- PostCheck.py: print a warning on empty script.
- FilesCheck.py: added postgres and apache to default users.
- TagsCheck.py: added bugs@linux-mandrake.com as a valid packager address.
- I18NCheck.py: check *.mo for file-not-in-%lang, not only in /usr/share/locale
- TagsCheck.py, MenuCheck.py: replaced Networking/ICQ group with Networking/Instant messaging.

* Thu Aug 31 2000 Frederic Lepied <flepied@mandrakesoft.com> 0.21-1mdk
- TagsCheck.py: check packager field compliance to a regexp.
- Config.py: imported default exceptions.
- TagsCheck.py: added Apache License, PHP Licence and BSD-Style.
- MenuCheck.py: check hardcoded path in icon field and large, mini, 
  normal icon files.
- PostCheck.py: Fix typo in check of /usr/bin/perl.
- PostCheck.py: Check perl script like we do for bash script.
- I18NCheck.py: updated locales list
- FilesCheck.py: Only check perl_temp_file in a /perl/ directory.

* Fri Aug 25 2000 Frederic Lepied <flepied@mandrakesoft.com> 0.20-1mdk
- InitScriptCheck.py: new check for /etc/rc.d/init.d scripts.
- PostCheck.py: check when a script is present that the shell is valid.
- ConfigCheck.py: report warnings for app-defaults only
in /usr/X11R6/lib/X11/app-defaults.
- BinariesCheck.py: report the rpath warning if the directory isn't a
sub-directory of /usr/lib/.

* Fri Aug 18 2000 Frederic Lepied <flepied@mandrakesoft.com> 0.19-1mdk
- BinariesCheck.py: check rpath only on system lib paths (ie /lib,
/usr/lib and /usr/X11R6/lib).  This can be configured with the
SystemLibPaths option.
- I18NCheck.py: warn if .mo is not registered in %%lang.
- MenuCheck.py: protected kdesu check.
- FilesCheck.py: check perl temporary files.
- rpmlint.py: added ExtractDir option usable in the config
file.
- PostCheck.py: check ] in if statement.  report warning for a
percent.

* Thu Aug 10 2000 Frederic Lepied <flepied@mandrakesoft.com> 0.18-1mdk
- TagsCheck: check licence file.
- ConfigCheck: check files without no-replace flag.
- MenuCheck: allow depency on kdesu to point directly to /usr/bin/kdesu.
- FHSCheck: allow ftp and www in var (from upcoming FHS 2.2).

* Tue Aug  8 2000 Frederic Lepied <flepied@mandrakesoft.com> 0.17-1mdk
- PostCheck: check bourne shell syntax (Chmouel).
- FileCheck: o check chkconfig calls for packages with a file in
             /etc/rc.d/init.d.
             o allow the call to install-info to be in %%preun.
- MenuCheck: o take care of kdesu (Chmouel).
- various exceptions added.

* Wed Jul 19 2000 Frederic Lepied <flepied@mandrakesoft.com> 0.16-1mdk
- FHSCheck activated by default.
- FileCheck: o check dangling symlinks.
             o check info/dir.

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
