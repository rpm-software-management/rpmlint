Name:           python-setup-install
Version:        1.0
Release:        0
Summary:        python-setup-install warning
License:        MIT
URL:            https://www.example.com
Source:         Source.tar.gz
BuildRequires:  gcc
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
A test specfile with python setup.py test that is deprecated.

%prep
%setup -q

%build
python3 setup.py build

%install
python3 setup.py install

%check

%files
%license COPYING
%doc ChangeLog README

%changelog
