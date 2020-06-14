Name:           broken-syntax-in-scriptlet-requires
Version:        0
Release:        0
Summary:        broken-syntax-in-scriptlet-requires warning
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz
Requires(post,preun): foo

%description
Comma separated context marked dependencies are silently broken in some
versions of rpm.  One way to work around it is to split them into several ones,
eg. replace 'Requires(post,preun): foo' with 'Requires(post): foo' and
'Requires(preun): foo'.

%prep
  %autosetup

%build

%install

%files
%{_libdir}/foo

%changelog
