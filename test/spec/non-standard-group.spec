Name:           non-standard-group
Version:        1.0
Release:        0
Summary:        non-standard-group warning
License:        MIT
Group:          Something
URL:            https://www.example.com
Source:         Source.tar.gz
BuildRequires:  gcc

%description
A test specfile with Group (Group: Something) that is not standard. The value of the Group tag in the package is not valid.

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
