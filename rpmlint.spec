#############################################################################
# File		: rpmlint.spec
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Tue Sep 28 07:18:06 1999
# Version	: $Id$
# Purpose	: rules to create the rpmlint binary package.
#############################################################################
%define name rpmlint
%define version 0.4
%define release 1mdk

Summary: rpm correctness checker
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.bz2
URL: http://www.lepied.com/rpmlint/
Copyright: GPL
Group: Development/System
BuildRoot: /tmp/%{name}-buildroot
Prefix: %{_prefix}
Requires: python >= 1.5.2, rpm-devel >= 3.0.3-35mdk, binutils, file, findutils, cpio
BuildArchitectures: noarch

%description
rpmlint is a tool to check common errors on rpm packages.
Only binary packages are supported for the moment.


%prep
%setup -q

%build
make

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT

find $RPM_BUILD_ROOT/ -type 'f'|grep -E '.*[0-9]'|xargs file|grep troff\
|cut -d: -f1|xargs bzip2 -9
for aa in man X11R6/man local/man;do
[ -d $RPM_BUILD_ROOT/usr/$aa ] || continue
for i in $(find $RPM_BUILD_ROOT/usr/$aa -type 'l');do
 	TO=$(/bin/ls -l $i|awk '{print $NF}')
	ln -sf $TO.bz2 $i && mv $i $.bz2
done
done
for i in `find $RPM_BUILD_ROOT/ -type 'f' -perm '+a=x' ! -name 'lib*so*'`;do
    file $i|grep -q "not stripped" && strip $i
done


%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,0755)
%{prefix}/bin/*
%{prefix}/share/rpmlint

%changelog

* Thu Oct  7 1999 Frederic Lepied <flepied@mandrakesoft.com>

- version 0.4: pgp check and group name check.

* Wed Oct  6 1999 Frederic Lepied <flepied@mandrakesoft.com>

- version 0.3.

* Mon Oct  4 1999 Frederic Lepied <flepied@mandrakesoft.com>

- version 0.2.

* Fri Oct  1 1999 Frederic Lepied <flepied@mandrakesoft.com>

- First spec file for Mandrake distribution.

# rpmlint.spec ends here
