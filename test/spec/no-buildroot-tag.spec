Name:           no-buildroot-tag
Version:        0
Release:        0
Summary:        no-buildroot-tag warning

Group:          Undefined
License:        GPLv2

%description
The BuildRoot tag isn't used in your spec. It must be used in order to
allow building the package as non root on some systems. For some rpm versions
(e.g. rpm.org >= 4.6) the BuildRoot tag is not necessary in specfiles and is
ignored by rpmbuild; if your package is only going to be built with such rpm
versions you can ignore this warning.

%files
%defattr(-,root,root,-)
%{_libdir}/foo

%changelog
