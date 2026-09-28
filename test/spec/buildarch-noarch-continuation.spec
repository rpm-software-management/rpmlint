Name:           buildarch-noarch-continuation
Version:        0
Release:        0
Summary:        BuildArch with line-continuation backslash
Group:          Undefined
License:        GPLv2
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz

# The BuildArch tag lives inside a multi-line macro, so its line ends
# with a line-continuation backslash (the libreoffice case from #698).
%define _set_buildarch() \
BuildArch:      noarch \
%{nil}
%_set_buildarch

BuildArchitectures: x86_64 \

%description
BuildArch with a trailing line-continuation backslash must not be
reported when the architecture is noarch; a real architecture with a
continuation still must be reported.

%prep

%build

%install

%files

%changelog
