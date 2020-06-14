Name:           non-break-space
Version:        0
Release:        0
Summary:        non-break-space warning.
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz

%description
The spec file contains a non-break space, which looks like a regular space
in some editors but can lead to obscure errors. It should be replaced by a
regular space.

%prep

%build

%install

%files
%{_libdir}/foo

%changelog
