Name:           python-setup-python_install
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
%python_build

%install
%python_install
%python3_install
%python312_install
# old fedora version
%py3_install

%check

%files
%license COPYING
%doc ChangeLog README

%changelog
