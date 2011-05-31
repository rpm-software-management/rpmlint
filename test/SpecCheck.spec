Name:           SpecCheck
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
Provides:       unversioned-provides, versioned-provides = 1.0
Obsoletes:      versioned-obsoletes < 2.0
Obsoletes:      unversioned-obsoletes

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
sed -e s/foo/bar/ %{PATCH5} | %{__patch} -p1


%build
# %configure
# %%%


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
