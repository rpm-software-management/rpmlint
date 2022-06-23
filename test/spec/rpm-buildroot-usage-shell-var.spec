Name:           rpm-buildroot-usage-shell-var
Version:        0
Release:        0
Summary:        rpm-buildroot-usage warning (when referenced as shell variable).
Group:          Undefined
License:        GPLv2
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
$RPM_BUILD_ROOT should not be touched during %build or %prep stage, as it
may break short circuit builds.

%prep
# None of these actually refer to the build root
\$RPM_BUILD_ROOT
\\\$RPM_BUILD_ROOT
# $RPM_BUILD_ROOT

%build
\\$RPM_BUILD_ROOT
echo ${RPM_BUILD_ROOT} # comment

%install

%clean

%files
%defattr(-,root,root,-)
%{_libdir}/foo

%changelog
