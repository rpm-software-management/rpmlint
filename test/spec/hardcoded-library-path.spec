Name:           hardcoded-library-path
Version:        0
Release:        0
Summary:        hardcoded-library-path error

Group:          Undefined
License:        GPLv2
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
A library path is hardcoded to one of the following paths: /lib,
/usr/lib. It should be replaced by something like /%{_lib} or %{_libdir}.

%prep
  %autosetup

%build
/usr/lib/bash/dirname/
/usr/lib
/lib

%clean

%files
%defattr(-,root,root,-)
%{_libdir}/foo

%changelog
