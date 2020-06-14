Name:           unversioned-explicit-provides
Version:        0
Release:        0
Summary:        unversioned-explicit-provides warning.

Group:          Undefined
License:        GPLv2
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Provides:       someones-something=%{version}
 
%description
The specfile contains an unversioned Provides: token, which will match all
older, equal, and newer versions of the provided thing. This may cause
update problems and will make versioned dependencies, obsoletions and conflicts
on the provided thing useless -- make the Provides versioned if possible.

%prep
  %autosetup

%build

%install
rm -rf $RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{_libdir}/foo

%changelog
