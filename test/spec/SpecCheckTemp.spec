# 1. rpm-buildroot-usage: 
#    %{buildroot} should not be touched during %build or %prep stage, 
#    as it may break short circuit builds.
# Developer Note:- This file contains %buildroot under %build macro 
#    since rpm-buildroot-usage.spec contains the
#    %build under %prep macro and we need to test "a warning if 
#    %{buildroot} is placed under %build".
# 
# 2. make-check-outside-check-section:
#    Make check or other automated regression test should be run 
#    in %check, as they can be disabled with a rpm macro for short
#    circuiting purposes.
# Developer Note:- This file contains `make check` inside %check 
#    %description %package %changelog to test the required check 
#    not in out.
# 
# 3. setup-not-quiet:
#    Use the -q option to the %setup macro to avoid useless 
#    build output from unpacking the sources.
# Developer Note:- This file contains the %setup -q macro to test 
#    the required check not in out.
#
# 4. setup-not-in-prep:
#     The %setup macro should only be used within the %prep 
#     section because it may not expand to anything outside
#     of it and can break the build in unpredictable.
# Developer Note:- This file contains %setup -q inside %prep 
#    macro to test if check setup-not-in-prep is not in out.
#
# 5. %autopatch-not-in-prep:
# Developer Note:- This file contains %autopatch inside the %prep macro.
#
# 6. %autosetup-not-in-prep:
# Developer Note:- This file contains %autosetup inside the %prep macro.
#
# 7. comparision-operator-in-deptoken:
#     This dependency token contains a comparison operator (<, > or =). 
#     This is usually not intended and may be caused by missing 
#     whitespace between the token's name, the comparison operator and 
#     the version strig.
# Developer Note:- This file contains < and <= operators as seen in 
#     Requires and Conflicts respectively and is responsible for 
#     respective check since it does not contains spaces around the operators.
%define __find_provides
%define _use_internal_dependency_generator 0

Name:           SpecCheckTemp
Version:        0
Release:        0
Summary:        rpm-buildroot-usage, make-check-outside-check, setup-not-quite, setup-not-in-prep, %autopatch-not-in-prep, %autosetup-not-in-prep warning, comparision-operator-in-deptoken.
License:        GPL-2.0-only
Group:          Undefined
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz
Requires:       Someotherthing<1.0
Conflicts:      Someotherthing<=2.0
Obsoletes:      /something      

%description
make check
    egrep something

%build
%{buildroot}

%prep
%setup -q
%autopatch
%autosetup

%check
make check

%package
make check
    grep something
    grep -F Someotherthing
    grep -E something

%install

%files
%{_libdir}/foo
    fgrep -F something

%changelog
make check 
    egrep -E something
