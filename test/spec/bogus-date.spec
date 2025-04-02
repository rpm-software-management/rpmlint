### Based on macro-in-changelog.spec, I added the date information in changlog, as follows：
Name:           macro-in
Version:        0
Release:        0
Summary:        macro-in
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz

%description
Macros are expanded in %changelog too, which can in unfortunate cases lead
to the package not building at all, or other subtle unexpected conditions that
affect the build.  Even when that doesn't happen, the expansion results in
possibly 'rewriting history' on subsequent package revisions and generally
odd entries eg. in source rpms, which is rarely wanted. Avoid use of macros
in %changelog altogether, or use two '%'s to escape them, like '%%foo'.

%prep

%build

%install

%files
%{_libdir}/foo

%changelog
* Wed Oct 22 14:15:39 UTC 2019 - Frank Schreiner <frank@fs.samaxi.de>
-
