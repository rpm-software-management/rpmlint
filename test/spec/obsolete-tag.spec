Name:           obsolete-tag
Version:        0
Release:        0
Summary:        obsolete-tag warning.
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz
Serial:         2
Copyright:      Something

%description
The following tags are obsolete: Copyright and Serial. They must
be replaced by License and Epoch respectively.

%prep
  %autosetup

%build

%install

%files
%{_libdir}/foo

%changelog
