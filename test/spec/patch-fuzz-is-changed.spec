%define _default_patch_fuzz 2
Name:           patch-fuzz-is-changed
Version:        1.0
Release:        0
Summary:        patch-fuzz-is-changed warning
License:        MIT
URL:            https://www.example.com
Source:         Source.tar.gz
BuildRequires:  gcc

%description
The internal patch fuzz value was changed, and could hide patchs issues, or
could lead to applying a patch at the wrong location. Usually, this is often
the sign that someone didn't check if a patch is still needed and do not want
to rediff it. It is usually better to rediff the patch and try to send it

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
