Name:           setup-not-quiet
Version:        0
Release:        0
Summary:        setup-not-quiet warning.
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz

%description
Use the -q option to the %setup macro to avoid useless build output from
unpacking the sources.

%prep

%setup

%build

%install

%files
%{_libdir}/foo

%changelog
