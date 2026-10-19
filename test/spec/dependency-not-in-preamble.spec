Name:           dependency-not-in-preamble
Version:        0
Release:        0
Summary:        Dummy test package

Group:          Undefined
License:        GPLv2

Requires:       this-requires-will-be-evaluated

%description
A dependency related tag comes after the preamble section ends for one package.
It will not be evaluated as a result. A valid package not preinstalled in the
build environment will not be available, and a invalid package will fail to block
the build.

Provides:       this-provides-will-not-be-evaluated
Requires:       this-requires-will-not-be-evaluated

%files
%defattr(-,root,root,-)
%{_libdir}/foo

%changelog
