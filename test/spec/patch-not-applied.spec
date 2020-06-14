Name:			patch-not-applied
Version:        0
Release:        0
Summary:		invalid-url warning
License:        GPL-2.0-only
Group:          Undefined
Patch0:         Patch.patch
Patch1:         Patch1.patch

%description
A patch is included in your package but was not applied.

%prep

%build

%install
%patch -P

%files
%{_libdir}/foo

%changelog
