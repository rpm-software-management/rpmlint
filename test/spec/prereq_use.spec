Name:           prereq_use
Version:        0
Release:        0
Summary:        prereq_use warning
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz
Patch0:         Patch0.patch
PreReq(pre):    none
PreReq(post):   none_other

%description
The use of PreReq is deprecated. In the majority of cases, a plain Requires
is enough and the right thing to do. Sometimes Requires(pre), Requires(post),
Requires(preun) and/or Requires(postun) can also be used instead of PreReq.

%prep
cd lib

%autopatch
%autosetup

%build

%install
%ifarch
# apply patch0
%patch0 -p0
%endif

%files
%{_libdir}/foo

%changelog
