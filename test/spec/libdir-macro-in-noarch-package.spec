Name:           libdir-macro-in-noarch-package
Version:        0
Release:        0
Summary:        libdir-macro-in-noarch-packagew warning
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz
BuildArch:      noarch

%description
The %{_libdir} or %{_lib} macro was found in a noarch package in a section
that gets included in binary packages.  This is most likely an error because
these macros are expanded on the build host and their values vary between
architectures, probably resulting in a package that does not work properly
on all architectures at runtime. Investigate whether the package is really
architecture independent or if some other dir/macro should be instead.

%prep

%build

%install

%files
%{_libdir}/foo

%changelog
