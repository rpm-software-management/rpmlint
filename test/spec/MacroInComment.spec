Name:           MacroInComment
Version:        0
Release:        0
Summary:        None here

Group:          Undefined
License:        GPLv2
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Provides:       unversioned-provides, versioned-provides = 1.0
Obsoletes:      versioned-obsoletes < 2.0
Obsoletes:      unversioned-obsoletes
Obsoletes:      /usr/bin/unversioned-but-filename
Provides:       /sbin/another-unversioned-but-filename
#!BuildIgnore:  %{name}

%description
MacroInComment test.

%package        noarch-sub
Summary:        Noarch subpackage
Group:          Undefined
BuildArch:      noarch

%description    noarch-sub
Noarch subpackage test.

%prep
%autosetup -p 1

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
