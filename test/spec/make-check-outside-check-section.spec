Name:           make-check-outside-check-section
Version:        0
Release:        0
Summary:        make-check-outside-check-section warning.
Group:          Undefined
License:        GPLv2
URL:            http://rpmlint.zarb.org/#%{name}

%description
Make check or other automated regression test should be run in %check, as
they can be disabled with a rpm macro for short circuiting purposes

%prep

make check

%check

%changelog
