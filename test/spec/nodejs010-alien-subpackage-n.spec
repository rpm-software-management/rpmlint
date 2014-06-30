%global scl nodejs010
%scl_package %scl
%global install_scl 1

Summary: %scl Software Collection
Name: %scl_name
Version: 1
Release: 7%{?dist}

Source1: macros.nodejs
Source2: nodejs.attr
Source3: nodejs.prov
Source4: nodejs.req
Source5: nodejs-symlink-deps
Source6: nodejs-fixdep
Source7: nodejs_native.attr

License: GPLv2+

%if 0%{?install_scl}
Requires: %{scl_prefix}nodejs
%endif

BuildRequires: scl-utils-build
BuildRequires: python-devel

%description
This is the main package for %scl Software Collection.

%package runtime
Summary: Package that handles %scl Software Collection.
Requires: scl-utils

%description runtime
Package shipping essential scripts to work with %scl Software Collection.

%package -n hehe
Summary: Package that should not be here
Requires: bullshit

%description hehe
This package should not be in SCL metapackage.

%package build
Summary: Package shipping basic build configuration
Requires: scl-utils-build

%description build
Package shipping essential configuration macros to build %scl Software Collection.

%prep
%setup -c -T

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_scl_scripts}/root
cat >> %{buildroot}%{_scl_scripts}/enable << EOF
export PATH=%{_bindir}:\$PATH
export LD_LIBRARY_PATH=%{_libdir}:\$LD_LIBRARY_PATH
export PYTHONPATH=%{_scl_root}%{python_sitelib}:\$PYTHONPATH
EOF

# install rpm magic
install -Dpm0644 %{SOURCE1} %{buildroot}%{_root_sysconfdir}/rpm/macros.%{name}
install -Dpm0644 %{SOURCE2} %{buildroot}%{_rpmconfigdir}/fileattrs/%{name}.attr
install -pm0755 %{SOURCE3} %{buildroot}%{_rpmconfigdir}/%{name}.prov
install -pm0755 %{SOURCE4} %{buildroot}%{_rpmconfigdir}/%{name}.req
install -pm0755 %{SOURCE5} %{buildroot}%{_rpmconfigdir}/%{name}-symlink-deps
install -pm0755 %{SOURCE6} %{buildroot}%{_rpmconfigdir}/%{name}-fixdep
install -Dpm0644 %{SOURCE7} %{buildroot}%{_rpmconfigdir}/fileattrs/%{name}_native.attr


# ensure Requires are added to every native module that match the Provides from
# the nodejs build in the buildroot
cat << EOF > %{buildroot}%{_rpmconfigdir}/%{name}_native.req
#!/bin/sh
echo 'nodejs010-nodejs(abi) = %nodejs_abi'
echo 'nodejs010-nodejs(v8-abi) = %v8_abi'
EOF
chmod 0755 %{buildroot}%{_rpmconfigdir}/%{name}_native.req

cat << EOF > %{buildroot}%{_rpmconfigdir}/%{name}-require.sh
#!/bin/sh
%{_rpmconfigdir}/%{name}.req $*
%{_rpmconfigdir}/find-requires $*
EOF
chmod 0755 %{buildroot}%{_rpmconfigdir}/%{name}-require.sh

cat << EOF > %{buildroot}%{_rpmconfigdir}/%{name}-provide.sh
#!/bin/sh
%{_rpmconfigdir}/%{name}.prov $*
%{_rpmconfigdir}/find-provides $*
EOF
chmod 0755 %{buildroot}%{_rpmconfigdir}/%{name}-provide.sh

%scl_install

%files

%files runtime
%scl_files

%files build
%{_root_sysconfdir}/rpm/macros.%{scl}-config
%{_root_sysconfdir}/rpm/macros.%{name}
%{_rpmconfigdir}/fileattrs/%{name}*.attr
%{_rpmconfigdir}/%{name}*


%changelog
* Mon Apr 15 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 1-7
- Update macros and requires/provides generator to latest

* Wed Apr 10 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 1-6
- Fix rpm requires/provides generator paths
- Add requires to main meta package

* Mon Apr 08 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 1-5
- Make package architecture specific for libdir usage

* Mon Apr 08 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 1-4
- Add rpm macros and tooling

* Mon Apr 08 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 1-3
- Add proper scl-utils-build requires

* Fri Apr 05 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 1-2
- Add PYTHONPATH to configuration

* Tue Mar 26 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 1-1
- Initial version of the Node.js Software Collection
