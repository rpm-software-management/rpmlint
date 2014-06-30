%{?scl:%scl_package nodejs}
%{!?scl:%global pkg_name %{name}}

Name: %{?scl_prefix}nodejs
Version: 0.10.3
Release: 3%{?dist}
Summary: JavaScript runtime
License: MIT and ASL 2.0 and ISC and BSD
Group: Development/Languages
URL: http://nodejs.org/

# Exclusive archs must match v8
ExclusiveArch: %{ix86} x86_64 %{arm}

Source0: http://nodejs.org/dist/v%{version}/node-v%{version}.tar.gz

# V8 presently breaks ABI at least every x.y release while never bumping SONAME,
# so we need to be more explicit until spot fixes that
%global v8_ge 1:3.14.5.7
%global v8_lt 1:3.15
%global v8_abi 3.14

BuildRequires: %{?scl_prefix}v8-devel >= %{v8_ge}
BuildRequires: %{?scl_prefix}http-parser-devel >= 2.0
BuildRequires: %{?scl_prefix}libuv-devel
BuildRequires: %{?scl_prefix}c-ares-devel
BuildRequires: zlib-devel
# Node.js requires some features from openssl 1.0.1 for SPDY support
BuildRequires: openssl-devel

Requires: libfoo

#we need ABI virtual provides where SONAMEs aren't enough/not present so deps
#break when binary compatibility is broken
%global nodejs_abi 0.10
Provides: %{?scl_prefix}nodejs(abi) = %{nodejs_abi}
Provides: %{?scl_prefix}nodejs(v8-abi) = %{v8_abi}

#this corresponds to the "engine" requirement in package.json
Provides: %{?scl_prefix}nodejs(engine) = %{version}

# Node.js currently has a conflict with the 'node' package in Fedora
# The ham-radio group has agreed to rename their binary for us, but
# in the meantime, we're setting an explicit Conflicts: %{?scl_prefix}here
Conflicts: %{?scl_prefix}node <= 0.3.2-11

%description
Node.js is a platform built on Chrome's JavaScript runtime
for easily building fast, scalable network applications.
Node.js uses an event-driven, non-blocking I/O model that
makes it lightweight and efficient, perfect for data-intensive
real-time applications that run across distributed devices.

%package devel
Summary: JavaScript runtime - development headers
Group: Development/Languages
Requires: %{name} = %{version}-%{release}
Requires: %{?scl_prefix}libuv-devel %{?scl_prefix}http-parser-devel openssl-devel %{?scl_prefix}c-ares-devel zlib-devel

%description devel
Development headers for the Node.js JavaScript runtime.

%package docs
Summary: Node.js API documentation
Group: Documentation

%description docs
The API documentation for the Node.js JavaScript runtime.

%prep
%setup -q -n node-v%{version}

# Make sure nothing gets included from bundled deps:
# We only delete the source and header files, because
# the remaining build scripts are still used.

find deps/cares -name "*.c" -exec rm -f {} \;
find deps/cares -name "*.h" -exec rm -f {} \;

find deps/npm -name "*.c" -exec rm -f {} \;
find deps/npm -name "*.h" -exec rm -f {} \;

find deps/zlib -name "*.c" -exec rm -f {} \;
find deps/zlib -name "*.h" -exec rm -f {} \;

find deps/v8 -name "*.c" -exec rm -f {} \;
find deps/v8 -name "*.h" -exec rm -f {} \;

find deps/http_parser -name "*.c" -exec rm -f {} \;
find deps/http_parser -name "*.h" -exec rm -f {} \;

find deps/openssl -name "*.c" -exec rm -f {} \;
find deps/openssl -name "*.h" -exec rm -f {} \;

find deps/uv -name "*.c" -exec rm -f {} \;
find deps/uv -name "*.h" -exec rm -f {} \;


%build
# build with debugging symbols and add defines from libuv (#892601)
export CFLAGS='%{optflags} -g -D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64 \
    -I%{_includedir}'
export CXXFLAGS='%{optflags} -g -D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64 \
    -I%{_includedir}'
export LDFLAGS='%{optflags} -L%{_libdir}'

./configure --prefix=%{_prefix} \
           --shared-v8 \
           --shared-openssl \
           --shared-zlib \
           --shared-cares \
           --shared-libuv \
           --shared-http-parser \
           --without-npm \
           --without-dtrace

# Setting BUILDTYPE=Debug builds both release and debug binaries
make BUILDTYPE=Debug %{?_smp_mflags}

%install
rm -rf %{buildroot}

./tools/install.py install %{buildroot}

# and remove dtrace file again
rm -rf %{buildroot}/%{_prefix}/lib/dtrace

# Set the binary permissions properly
chmod 0755 %{buildroot}/%{_bindir}/node

# Install the debug binary and set its permissions
install -Dpm0755 out/Debug/node %{buildroot}/%{_bindir}/node_g

# own the sitelib directory
mkdir -p %{buildroot}%{_prefix}/lib/node_modules

#install documentation
mkdir -p %{buildroot}%{_defaultdocdir}/%{pkg_name}-docs-%{version}/html
cp -pr doc/* %{buildroot}%{_defaultdocdir}/%{pkg_name}-docs-%{version}/html
rm -f %{_defaultdocdir}/%{pkg_name}-docs-%{version}/html/nodejs.1
cp -p LICENSE %{buildroot}%{_defaultdocdir}/%{pkg_name}-docs-%{version}/

#install development headers
#FIXME: we probably don't really need *.h but node-gyp downloads the whole
#freaking source tree so I can't be sure ATM
mkdir -p %{buildroot}%{_includedir}/node
cp -p src/*.h %{buildroot}%{_includedir}/node

#node-gyp needs common.gypi too
mkdir -p %{buildroot}%{_datadir}/node
cp -p common.gypi %{buildroot}%{_datadir}/node

%files
%doc ChangeLog LICENSE README.md AUTHORS
%{_bindir}/node
%{_mandir}/man1/node.*
%dir %{_prefix}/lib/node_modules

%files devel
%{_bindir}/node_g
%{_includedir}/node
%{_datadir}/node

%files docs
%{_defaultdocdir}/%{pkg_name}-docs-%{version}

%changelog
* Mon Apr 08 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 0.10.3-3
- Add support for software collections
- Move rpm macros and tooling to separate package

* Thu Apr 04 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.3-2
- nodejs-symlink-deps: symlink unconditionally in the buildroot

* Wed Apr 03 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.3-1
- new upstream release 0.10.3
  http://blog.nodejs.org/2013/04/03/node-v0-10-3-stable/
- nodejs-symlink-deps: only create symlink if target exists
- nodejs-symlink-deps: symlink devDependencies when --check is used

* Sun Mar 31 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.2-1
- new upstream release 0.10.2
  http://blog.nodejs.org/2013/03/28/node-v0-10-2-stable/
- remove %%nodejs_arches macro since it will only be useful if it is present in
  the redhat-rpm-config package
- add default filtering macro to remove unwanted Provides from native modules
- nodejs-symlink-deps now supports multiple modules in one SRPM properly
- nodejs-symlink-deps also now supports a --check argument that works in the
  current working directry instead of the buildroot

* Fri Mar 22 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.1-1
- new upstream release 0.10.1
  http://blog.nodejs.org/2013/03/21/node-v0-10-1-stable/

* Wed Mar 20 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.0-4
- fix escaping in dependency generator regular expressions (RHBZ#923941)

* Wed Mar 13 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.0-3
- add virtual ABI provides for node and v8 so binary module's deps break when
  binary compatibility is broken
- automatically add matching Requires to nodejs binary modules
- add %%nodejs_arches macro to future-proof ExcluseArch stanza in dependent
  packages

* Tue Mar 12 2013 Stephen Gallagher <sgallagh@redhat.com> - 0.10.0-2
- Fix up documentation subpackage

* Mon Mar 11 2013 Stephen Gallagher <sgallagh@redhat.com> - 0.10.0-1
- Update to stable 0.10.0 release
- https://raw.github.com/joyent/node/v0.10.0/ChangeLog

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.9.5-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Tue Jan 22 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.9.5-10
- minor bugfixes to RPM magic
  - nodejs-symlink-deps: don't create an empty node_modules dir when a module
    has no dependencies
  - nodes-fixdep: support adding deps when none exist
- Add the full set of headers usually bundled with node as deps to nodejs-devel.
  This way `npm install` for native modules that assume the stuff bundled with
  node exists will usually "just work".
-move RPM magic to nodejs-devel as requested by FPC

* Sat Jan 12 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.9.5-9
- fix brown paper bag bug in requires generation script

* Thu Jan 10 2013 Stephen Gallagher <sgallagh@redhat.com> - 0.9.5-8
- Build debug binary and install it in the nodejs-devel subpackage

* Thu Jan 10 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.9.5-7
- don't use make install since it rebuilds everything

* Thu Jan 10 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.9.5-6
- add %%{?isa}, epoch to v8 deps

* Wed Jan 09 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.9.5-5
- add defines to match libuv (#892601)
- make v8 dependency explicit (and thus more accurate)
- add -g to $C(XX)FLAGS instead of patching configure to add it
- don't write pointless 'npm(foo) > 0' deps

* Sat Jan 05 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.9.5-4
- install development headers
- add nodejs_sitearch macro

* Wed Jan 02 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.9.5-3
- make nodejs-symlink-deps actually work

* Tue Jan 01 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.9.5-2
- provide nodejs-devel so modules can BuildRequire it (and be consistent
  with other interpreted languages in the distro)

* Tue Jan 01 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.9.5-1
- new upstream release 0.9.5
- provide nodejs-devel for the moment
- fix minor bugs in RPM magic
- add nodejs_fixdep macro so packagers can easily adjust dependencies in
  package.json files

* Wed Dec 26 2012 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.9.4-1
- new upstream release 0.9.4
- system library patches are now upstream
- respect optflags
- include documentation in subpackage
- add RPM dependency generation and related magic
- guard libuv depedency so it always gets bumped when nodejs does
- add -devel subpackage with enough to make node-gyp happy

* Wed Dec 19 2012 Dan Horák <dan[at]danny.cz> - 0.9.3-8
- set exclusive arch list to match v8

* Tue Dec 18 2012 Stephen Gallagher <sgallagh@redhat.com> - 0.9.3-7
- Add remaining changes from code review
- Remove unnecessary BuildRequires on findutils
- Remove %%clean section

* Fri Dec 14 2012 Stephen Gallagher <sgallagh@redhat.com> - 0.9.3-6
- Fixes from code review
- Fix executable permissions
- Correct the License field
- Build debuginfo properly

* Thu Dec 13 2012 Stephen Gallagher <sgallagh@redhat.com> - 0.9.3-5
- Return back to using the standard binary name
- Temporarily adding a conflict against the ham radio node package until they
  complete an agreed rename of their binary.

* Wed Nov 28 2012 Stephen Gallagher <sgallagh@redhat.com> - 0.9.3-4
- Rename binary and manpage to nodejs

* Mon Nov 19 2012 Stephen Gallagher <sgallagh@redhat.com> - 0.9.3-3
- Update to latest upstream development release 0.9.3
- Include upstreamed patches to unbundle dependent libraries

* Tue Oct 23 2012 Adrian Alves <alvesadrian@fedoraproject.org>  0.8.12-1
- Fixes and Patches suggested by Matthias Runge

* Mon Apr 09 2012 Adrian Alves <alvesadrian@fedoraproject.org> 0.6.5
- First build.
