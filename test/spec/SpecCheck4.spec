Name:           SpecCheck4
Version:        0.0.1
Release:        0
Summary:        None here

Group:          Undefined
License:        GPLv2
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz
Requires:       require
Provides:       provide
Obsoletes:      obsolete
Conflicts:       conflict

%description

%prep
%setup -q

%build
%configure
%make_build

%install
%make_install

%post
%postun

%files
%license COPYING
%doc ChangeLog README

%changelog
* Wed Oct 23 14:15:39 UTC 2019 - Frank Schreiner <frank@fs.samaxi.de>
- changelog entry ....  
