Name:           SpecCheck_forbidden-controlchar-found 
Version:        1.0
Release:        0
Summary:        forbidden-controlchar-found warning
License:        MIT
URL:            https://www.example.com
Source:         Source.tar.gz
Requires:       something_needed > 1.0
Provides:       something_new
Obsoletes:      something_old
Conflicts:      something_bad
BuildRequires:  gcc

%description
This package contains tags which contain forbidden control characters.
These are all ASCII characters with a decimal value below 32, except TAB(9),
LF(10) and CR(13)

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
- This is a changelog entry with forbidden control character

