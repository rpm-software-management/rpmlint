%define __find_provides 

Name:           depscript-without-disabling-depgen
Version:        0
Summary:        depscript-without-disabling-depgen warning
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz

%description
In some common rpm configurations/versions, defining __find_provides and/or
__find_requires has no effect if rpm's internal dependency generator has not
been disabled for the build.  %define _use_internal_dependency_generator to 0
to disable it in the specfile, or don't define __find_provides/requires.

%prep
  %autosetup

%build

%install

%files
%{_libdir}/foo

%changelog
