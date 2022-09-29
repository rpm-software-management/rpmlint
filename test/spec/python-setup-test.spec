Name:           python-setup-test
Version:        1.0
Release:        0
Summary:        python-setup-test warning
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
%python_exec setup.py test

%post
%postun

%files
%license COPYING
%doc ChangeLog README

%changelog
