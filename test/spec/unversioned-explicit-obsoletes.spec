Name:           unversioned-explicit-obsoletes
Version:        0
Release:        0
Summary:        unversioned-explicit-obsoletes
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz
Obsoletes:      Something

%description
The specfile contains an unversioned Obsoletes: token, which will match all
older, equal and newer versions of the obsoleted thing.  This may cause update
problems, restrict future package/provides naming, and may match something it
was originally not inteded to match -- make the Obsoletes versioned if
possible.

%prep
  %autosetup

%build

%install

%files
%{_libdir}/foo

%changelog
