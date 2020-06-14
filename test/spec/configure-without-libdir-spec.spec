Name:           configure-without-libdir-spec
Version:        0
Release:        0
Summary:        configure-without-libdir-spec warning
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz

%description
A configure script is run without specifying the libdir. configure
options must be augmented with something like --libdir=%{_libdir} whenever
the script supports it.

%prep
  %autosetup

%build
./configure

%install

%files

%changelog
