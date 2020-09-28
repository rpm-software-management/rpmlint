Name:           SpecCheck2
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
BuildRequires:  source-for-second-rpm
BuildArch:      noarch
ExclusiveArch:  i586
Requires:       Oneanotherthing>=1.0
Conflicts:      Onelastthing==2.0

%description
macro-in-%changelog-deptoken:-
(Developer Note)
    Macro can cause a warning which you can escape by using %%buildroot or 
    %+buildroot or %.buildroot or any othersign prefixed with % 
    for example %(-, +, .) and so on.
    Make sure you exclude %_buildroot or usage of % followed by _

%prep
  %autosetup

%build
%configure
./configure --libdir=%{_libdir}
make %{_libdir}

%install
rm -rf $RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{_libdir}/foo

%changelog
