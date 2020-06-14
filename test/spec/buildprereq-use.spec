Name:           buildprereq-use
Version:        0
Release:        0
Summary:        buildprereq-use warning
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz
BuildPreReq:    Something

%description
The use of BuildPreReq is deprecated, build dependencies are always required
before a package can be built.  Use plain BuildRequires instead.

%prep
  %autosetup

%build

%install

%files
%{_libdir}/foo

%changelog
