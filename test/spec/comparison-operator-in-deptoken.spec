Name:           comparison-operator-in-deptoken
Version:        0
Release:        0
Summary:        comparison-operator-in-deptoken warning.

License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz
BuildRequires:  something>2.0
Requires:       Something>1.0
Conflicts:      Something=2.0

%description
This dependency token contains a comparison operator (<, > or =).  This is
usually not intended and may be caused by missing whitespace between the
token's name, the comparison operator and the version string.

%prep
  %autosetup

%build

%install

%files
%{_libdir}/foo

%changelog
