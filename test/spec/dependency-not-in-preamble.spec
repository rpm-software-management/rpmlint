Name:           dependency-not-in-preamble
Version:        0
Release:        0
Summary:        Dummy test package

Group:          Undefined
License:        GPLv2

Requires:       this-requires-will-be-evaluated

%description
A dependency-related tag after the preamble section will not be evaluated.
A valid package not preinstalled in the build environment will not be available,
and an invalid package will fail to block the build.

Provides:       this-provides-will-not-be-evaluated
Requires:       this-requires-will-not-be-evaluated

%package subpackage
Summary:        Dummy test subpackage

%description subpackage
The same applies for subpackages, which has its own preamble section.

Provides:       this-will-not-be-evaluated-either

%files
%defattr(-,root,root,-)
%{_libdir}/foo

%changelog
