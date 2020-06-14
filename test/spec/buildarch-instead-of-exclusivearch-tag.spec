Name:           buildarch-instead-of-exclusivearch-tag
Version:        0
Release:        0
Summary:        buildarch-instead-of-exclusivearch-tag warning

Group:          Undefined
License:        GPLv2
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz
BuildArch:      x86_64
BuildArchitectures: i586
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
Use ExclusiveArch instead of BuildArch (or BuildArchitectures)
to restrict build on some specific architectures.
Only use BuildArch with noarch

%prep
  %autosetup

%build

%install

%clean

%files
%defattr(-,root,root,-)
%{_libdir}/foo

%changelog
