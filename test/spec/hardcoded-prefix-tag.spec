Name:           hardcoded-prefix-tag
Version:        0
Release:        0
Summary:        hardcoded-prefix-tag warning
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz
Prefix:         /usr/bin/bash

%description
The Prefix tag is hardcoded in your spec file. It should be removed, so as
to allow package relocation.

%prep

%build

%install

%files
%{_libdir}/foo

%changelog
