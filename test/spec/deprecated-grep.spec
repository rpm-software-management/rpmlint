Name:           deprecated-grep
Version:        0
Release:        0
Summary:        deprecated-grep warning
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz

%description
Direct use of grep as egrep or fgrep is deprecated in GNU grep and
historical in POSIX, use grep -E and grep -F instead.

%prep
    egrep something 

%build

%install

%files
%{_libdir}/foo

%changelog
