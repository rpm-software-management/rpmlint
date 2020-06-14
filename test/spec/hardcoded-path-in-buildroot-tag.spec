Name:           hardcoded-path-in-buildroot-tag
Version:        0
Release:        0
Summary:        hardcoded-path-in-buildroot-tag warning.
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Buildroot:      /usr/bin/bash
Source0:        Source0.tar.gz

%description
A path is hardcoded in your Buildroot tag. It should be replaced
by something like %{_tmppath}/%{name}-%{version}-build.

%prep
  %autosetup

%build

%install

%files
%{_libdir}/foo

%changelog
