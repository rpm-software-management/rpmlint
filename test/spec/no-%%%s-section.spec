Name:           no-%%%s-section
Version:        0
Release:        0
Summary:        no-%%%s-section warning
License:        GPL-2.0-only
Group:          Undefined

%description
no-%prep-section:-
    The spec file does not contain a %prep section.  Even if some packages don't
    directly need it, section markers may be overridden in rpm's configuration
    to provide additional 'under the hood' functionality.  Add the section, even
    if empty.
no-%build-section:-
    The spec file does not contain a %build section.  Even if some packages
    don't directly need it, section markers may be overridden in rpm's
    configuration to provide additional 'under the hood' functionality, such as
    injection of automatic -debuginfo subpackages.  Add the section, even if
    empty.
no-%install-section:-
    The spec file does not contain an %install section.  Even if some packages
    don't directly need it, section markers may be overridden in rpm's
    configuration to provide additional 'under the hood' functionality.  Add the
    section, even if empty.
no-%{clean}-section:-
    The spec file doesn't contain a %{clean} section to remove the files installed
    by the %install section

%files
%{_libdir}/foo

%changelog
