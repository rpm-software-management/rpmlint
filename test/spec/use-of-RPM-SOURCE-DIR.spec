Name:           use-of-RPM-SOURCE-DIR
Version:        0
Release:        0
Summary:        use-of-RPM-SOURCE-DIR error
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz

%description
You use $RPM_SOURCE_DIR or %{_sourcedir} in your spec file. If you have to
use a directory for building, use %{buildroot} instead.

%prep
  %autosetup

%build

%{_sourcedir}

%install
rm -rf $RPM_SOURCE_DIR

%files
%{_libdir}/foo

%changelog
