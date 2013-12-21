Name:           SpecCheck3
Version:        0
Release:        0
Summary:        None here

Group:          Undefined
License:        GPLv2
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz
Patch:          Patch.patch
Patch1:         Patch1.patch
Patch2:         Patch2.patch
Patch3:         Patch3.patch
Patch4:         Patch4.patch
Patch5:         Patch5.patch
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
SpecCheck test 2.


%prep
%autosetup -N
  %autopatch


%build


%install
rm -rf $RPM_BUILD_ROOT


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%{_libdir}/foo


%changelog
