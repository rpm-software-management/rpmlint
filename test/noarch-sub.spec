Name:           noarch-sub
Version:        0
Release:        0
Summary:        -
Group:          Development/Debug
License:        -
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
-

%package        noarch
Summary:        -
Group:          Development/Debug
BuildArch:      noarch

%description    noarch
-


%prep


%build
%configure


%install
rm -rf $RPM_BUILD_ROOT


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%{_libdir}/foo

%files noarch
%defattr(-,root,root,-)


%changelog
