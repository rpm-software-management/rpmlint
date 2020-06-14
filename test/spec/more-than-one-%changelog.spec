Name:           more-than-one-%changelog-section
Version:        0
Release:        0
Summary:        more-than-one-%changelog-section
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz

%description
The spec file unnecessarily contains more than one %changelog section.

%prep
  %autosetup

%build

%install

%files
%{_libdir}/foo

%changelog
something.
%changelog
one another thing.
