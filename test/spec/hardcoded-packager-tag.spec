Name:           hardcoded-packager-tag
Version:        0
Release:        0
Summary:        hardcoded-packager-tag warning
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz
Packager:       Someone

%description
The Packager tag is hardcoded in your spec file. It should be removed, so
as to use rebuilder's own defaults.

%prep

%build

%install

%files
%{_libdir}/foo

%changelog
