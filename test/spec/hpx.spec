#
# spec file for package hpx
#
# Copyright (c) 2023 SUSE LLC
# Copyright (c) 2019 Christoph Junghans
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/
#


Name:           hpx
Version:        1.8.1
Release:        0
Summary:        General Purpose C++ Runtime System
License:        BSL-1.0
Group:          Productivity/Networking/Other
URL:            https://stellar.cct.lsu.edu/tag/hpx/
Source0:        https://github.com/STEllAR-GROUP/hpx/archive/%{version}.tar.gz#/%{name}_%{version}.tar.gz
Patch1:         Add-missing-header-for-std-intmax_t.patch
BuildRequires:  asio-devel
BuildRequires:  cmake
BuildRequires:  fdupes
BuildRequires:  gcc-c++
BuildRequires:  gperftools-devel
BuildRequires:  hwloc-devel
BuildRequires:  libboost_atomic-devel
BuildRequires:  libboost_filesystem-devel
BuildRequires:  libboost_iostreams-devel
BuildRequires:  libboost_program_options-devel
BuildRequires:  libboost_regex-devel
BuildRequires:  libboost_system-devel
%ifarch aarch64 %{arm}
BuildRequires:  libboost_chrono-devel
BuildRequires:  libboost_context-devel
BuildRequires:  libboost_thread-devel
%endif
BuildRequires:  openmpi-macros-devel
Requires:       libhpx1 = %{version}-%{release}

%description
HPX is a general purpose C++ runtime system for parallel and distributed applications of any scale.

%package devel
Summary:        Development headers and libraries for hpx
Group:          Development/Libraries/C and C++
Requires:       libhpx1 = %{version}-%{release}
%{openmpi_devel_requires}

%description devel
HPX is a general purpose C++ runtime system for parallel and distributed applications of any scale.

This package contains development headers and libraries for hpx

%package -n libhpx1
Summary:        Libraries for the hpx package
Group:          System/Libraries
%{openmpi_requires}

%description -n libhpx1
HPX is a general purpose C++ runtime system for parallel and distributed applications of any scale.

This package contains libraries for the hpx package.

%prep
%define _lto_cflags %{nil}
%setup -q
%patch1

%build
%ifarch aarch64 %{arm}
%define cmake_opts -DHPX_WITH_GENERIC_CONTEXT_COROUTINES=ON
%endif

# add lib atomic for s390x and ppc64
%ifarch s390x ppc64
%define cmake_opts -DCMAKE_SHARED_LINKER_FLAGS="%{optflags} -Wl,--push-state,--no-as-needed -latomic -Wl,--pop-state" -DCMAKE_EXE_LINKER_FLAGS="%{optflags} -Wl,--push-state,--no-as-needed -latomic -Wl,--pop-state"
%endif

%{setup_openmpi}
%cmake -DLIB=%{_lib} %{?cmake_opts:%cmake_opts} \
 -DHPX_WITH_BUILD_BINARY_PACKAGE=ON \
 -DHPX_WITH_EXAMPLES=OFF
make -j1

%install
make -C build install DESTDIR=%{buildroot}
rm %{buildroot}/%{_datadir}/%{name}/LICENSE_1_0.txt
# Remove static libs and extra binaries
rm -f %{buildroot}/%{_libdir}/*.a
rm -f %{buildroot}/%{_bindir}/hpx_run_test.py
%fdupes %{buildroot}%{_prefix}

sed -i '1s@env @@' %{buildroot}/%{_bindir}/{hpx*.py,hpxcxx}

%post -n libhpx1 -p /sbin/ldconfig
%postun -n libhpx1 -p /sbin/ldconfig

%files
%{_bindir}/hpx*.py
%doc README.rst
%license LICENSE_1_0.txt

%files -n libhpx1
%license LICENSE_1_0.txt
%dir %{_libdir}/%{name}/
%{_libdir}/%{name}/lib*.so.*
%{_libdir}/lib*.so.*

%files devel
%{_bindir}/hpxcxx
%{_includedir}/%{name}
%{_libdir}/lib*.so
%{_libdir}/%{name}/lib*.so
%{_libdir}/pkgconfig/*.pc
%{_libdir}/cmake/HPX

%changelog
