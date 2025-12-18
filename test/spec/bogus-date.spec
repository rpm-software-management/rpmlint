### Based on macro-in-changelog.spec, I added the date information in changlog, as follows：
Name:           bogus-date
Version:        0
Release:        0
Summary:        bogus-date
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz

%description
The 'rpm -q --specfile' command will display a warning message if the day of the
week or date is not set correctly in %changelog.
For example:'warning: bogus date in %changelog'

%prep

%build

%install

%files
%{_libdir}/foo

%changelog
* Wed Oct 22 14:15:39 UTC 2019 - Frank Schreiner <frank@fs.samaxi.de>
-
