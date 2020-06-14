Name:           %autopatch-not-in-prep
Version:        0
Release:        0
Summary:        autopatch not inside prep warning
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz
Requires:       Somethingwithsinglespace >=1.0
Conflicts:      Someotherthinwithsinglespace<= 1.0
Obsoletes:      %{name} <= %{version}
Provides:       %{name} = %{version}

%description
autopatch macro must be inside %prep.

%autopatch

%prep

%build

%install

%files
%{_libdir}/foo

%changelog
