Name:           setup-not-in-prep
Version:        0
Release:        0
Summary:        setup-not-in-prep warning
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz

%description
The %setup macro should only be used within the %prep section because it may
not expand to anything outside of it and can break the build in unpredictable.

%setup

%prep

%build

%files
%{_libdir}/foo

%changelog
