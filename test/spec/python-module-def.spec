%{?!python_module:%define python_module() python-%{**} python3-%{**}}

Name:           python-module-def
Version:        1.0
Release:        0
Summary:        python-module-def warning
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
%configure
%make_build

%install
%make_install

%check
%pytest

%post
%postun

%files
%license COPYING
%doc ChangeLog README

%changelog
