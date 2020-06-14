Name:           %ifarch-applied-patch
Version:        0
Release:        0
Summary:        %ifarch-applied-patch warning
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz
Patch1:         Patch1.patch
Requires(post): foo

%description
A patch is applied inside an %ifarch block. Patches must be applied
on all architectures and may contain necessary configure and/or code
patch to be effective only on a given arch.

%prep

%build

%install
%ifarch
%patch1 -P 1
%endif

%files
%{_libdir}/foo

%changelog
