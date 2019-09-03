Name:		missingprovides-devel
Version:	0
Release:	0
Group:          Games
Summary:	Lorem ipsum
License:	GPL-2.0+
BuildRoot:	%_tmppath/%name-%version-build
Url:            http://www.opensuse.org/
%if 0%{?suse_version} > 123
echo "xxx"
Requires: xinetd
%if 0%{?suse_version} > 123456789
echo "xxx"
Requires: xinetd
%endif
%if %suse_version > 567
echo "xxx"
Requires: xinetd
%if %suse_version > 56789
echo "xxx"
Requires: xinetd
%endif


%description
Lorem ipsum dolor sit amet, consectetur adipisici elit, sed
eiusmod tempor incidunt ut labore et dolore magna aliqua. Ut enim
ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
aliquid ex ea commodi consequat. Quis aute iure reprehenderit in
voluptate velit esse cillum dolore eu fugiat nulla pariatur.
Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui
officia deserunt mollit anim id est laborum.

%prep
%build


%install
mkdir -p %buildroot/usr/lib64/pkgconfig/
echo "" >> %buildroot/usr/lib64/pkgconfig/libparted.pc

%clean
rm -rf %buildroot

%files
/usr/lib64/pkgconfig/libparted.pc

%changelog
* Mon Apr 18 2011 lnussel@suse.de
- dummy
