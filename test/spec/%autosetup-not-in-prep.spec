# This is comment to check macro-in-comment not found.
Name:           autosetup-not-in-prep
Version:        0
Release:        0
Summary:        autosetup-not-in-prep warning.
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz
Requires:       Somethingwithdoublespace = 1.0
Conflicts:      Some thing with double space == 2.0
Provides:       /Something

%description
The specfile contains %autosetup outside the %prep.

%autosetup

%prep

%build

%install

%files
%{_libdir}/foo

%changelog
