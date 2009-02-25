Name:           SpecCheck
Version:        0
Release:        0
Summary:        None here

Group:          Undefined
License:        GPLv2
URL:            http://rpmlint.zarb.org/
Source0:        Source0.tar.gz
Patch:          Patch.patch
Patch1:         Patch1.patch
Patch2:         Patch2.patch
Patch3:         Patch3.patch
Patch4:         Patch4.patch
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
SpecCheck test.

%package        noarch-sub
Summary:        Noarch subpackage
Group:          Undefined
BuildArch:      noarch

%description    noarch-sub
Noarch subpackage test.


%prep
%setup -q
%patch1
%patch
%patch -P 2 -P 4

%build


%install
rm -rf $RPM_BUILD_ROOT


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%{_libdir}/foo

%files noarch-sub
%defattr(-,root,root,-)


%changelog
