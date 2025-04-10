#
# spec file for package yast2-installation
#
# Copyright (c) 2024 SUSE LLC
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


Name:           yast2-installation
Version:        5.0.15
Release:        0
Summary:        YaST2 - Installation Parts
License:        GPL-2.0-only
Group:          System/YaST
URL:            https://github.com/yast/yast-installation
Source0:        %{name}-%{version}.tar.bz2
Source1:        YaST2-Second-Stage.service
Source2:        YaST2-Firstboot.service

BuildRequires:  update-desktop-files
# Kernel: Use is_zvm from Yast::Arch
BuildRequires:  yast2 >= 5.0.5
# systemd-boot kernel parameters
BuildRequires:  yast2-bootloader >= 5.0.9
# storage-ng based version
BuildRequires:  yast2-country >= 3.3.1
BuildRequires:  yast2-devtools >= 3.1.10
# For firewall widgets
BuildRequires:  yast2-firewall
# Y2Network::ProposalSettings #modify_defaults and #apply_defaults (forwarding configurable)
BuildRequires:  yast2-network >= 4.4.12
# ProductSpec API
BuildRequires:  yast2-packager >= 4.4.13
# yast/rspec/helpers.rb
BuildRequires:  yast2-ruby-bindings >= 4.4.7
# Support for SecurityPolicies
BuildRequires:  yast2-security >= 4.5.3
# using /usr/bin/udevadm
BuildRequires:  yast2-storage-ng >= 4.2.71
# Y2Users
BuildRequires:  yast2-users >= 4.4.2
# needed for xml agent reading about products
BuildRequires:  yast2-xml
BuildRequires:  rubygem(%{rb_default_ruby_abi}:rspec)
BuildRequires:  rubygem(%{rb_default_ruby_abi}:yast-rake)
# Augeas lenses
Requires:       augeas-lenses
Requires:       coreutils
Requires:       gzip
# use in startup scripts
Requires:       initviocons
# bsc#1214277; require awk, not gawk, to allow for lighterweight alternatives like busybox
Requires:       awk
# Needed call /sbin/ip in vnc.sh/network.sh
Requires:       iproute2
# for the first/second stage of installation
# currently not used
# bugzilla #208307
#Requires:      /usr/bin/jpegtopnm
#Requires:      /usr/bin/pnmtopng
# BNC 446533, /sbin/lspci called but not installed
Requires:       pciutils
# tar-gzip some system files and untar-ungzip them after the installation (FATE #300421, #120103)
Requires:       tar
# /usr/lib/YaST2/bin/xftdpi, install only when the GUI is installed
Requires:       (yast2-x11 >= 4.5.1 if libyui-qt)
# Y2Packager::Repository.refresh
Requires:       yast2 >= 5.0.3
Requires:       yast2-bootloader >= 5.0.9
Requires:       yast2-country >= 3.3.1
# Language::GetLanguageItems and other API
# Language::Set (handles downloading the translation extensions)
Requires:       yast2-country-data >= 2.16.11
# Y2Network::ProposalSettings #modify_defaults and #apply_defaults (forwarding configurable)
Requires:       yast2-network >= 4.4.12
# ProductSpec API
Requires:       yast2-packager >= 4.4.13
# Pkg::ProvidePackage
Requires:       yast2-pkg-bindings >= 3.1.33
# Proxy settings for 2nd stage (bnc#764951)
Requires:       yast2-proxy >= 4.4.1
# for AbortException and handle direct abort
Requires:       yast2-ruby-bindings >= 4.0.6
# Systemd default target and services. This version supports
# writing settings in the first installation stage.
Requires:       yast2-services-manager >= 3.2.1
# Only in inst-sys
Requires:       yast2-storage-ng >= 4.0.175
# Y2Users
Requires:       yast2-users >= 4.4.2
# Support for SecurityPolicies
Requires:       yast2-security >= 4.5.3
PreReq:         %fillup_prereq
Recommends:     yast2-add-on
Recommends:     yast2-firewall
Recommends:     yast2-online-update
Supplements:    autoyast(deploy_image:ssh_import)
# new autoinst_files_finish call
Conflicts:      autoyast2 < 4.3.26
# SingleItemSelector not enforcing an initial selection
Conflicts:      libyui < 3.8.2
# InstError
Conflicts:      yast2 < 2.18.6
# storage-ng based version
Conflicts:      yast2-bootloader < 3.3.1
# Added new function WFM::ClientExists
Conflicts:      yast2-core < 2.17.10
# Mouse-related scripts moved to yast2-mouse
Conflicts:      yast2-mouse < 2.18.0
# Pkg::SourceProvideSignedFile Pkg::SourceProvideDigestedFile
# pkg-bindings are not directly required
Conflicts:      yast2-pkg-bindings < 2.17.25
# Registration#get_updates_list does not handle exceptions
Conflicts:      yast2-registration < 3.2.3
# Top bar with logo
Conflicts:      yast2-ycp-ui-bindings < 3.1.7
Obsoletes:      yast2-installation-devel-doc
# we provide here only client that is used in microos from caasp package
# and those clients conflicts on file level
Conflicts:      yast2-caasp <= 5.0.0
BuildArch:      noarch
%if 0%{?suse_version} >= 1210
%{systemd_requires}
%endif

%description
System installation code as present on installation media.

%prep
%setup -q

%check
%yast_check

%build

%install
%yast_install
%yast_metainfo

for f in `find %{buildroot}%{_datadir}/autoinstall/modules -name "*.desktop"`; do
    %suse_update_desktop_file $f
done

mkdir -p %{buildroot}%{yast_vardir}/hooks/installation
mkdir -p %{buildroot}%{yast_ystartupdir}/startup/hooks/preFirstCall
mkdir -p %{buildroot}%{yast_ystartupdir}/startup/hooks/preSecondCall
mkdir -p %{buildroot}%{yast_ystartupdir}/startup/hooks/postFirstCall
mkdir -p %{buildroot}%{yast_ystartupdir}/startup/hooks/postSecondCall
mkdir -p %{buildroot}%{yast_ystartupdir}/startup/hooks/preFirstStage
mkdir -p %{buildroot}%{yast_ystartupdir}/startup/hooks/preSecondStage
mkdir -p %{buildroot}%{yast_ystartupdir}/startup/hooks/postFirstStage
mkdir -p %{buildroot}%{yast_ystartupdir}/startup/hooks/postSecondStage

mkdir -p %{buildroot}%{_unitdir}
install -m 644 %{SOURCE1} %{buildroot}%{_unitdir}
install -m 644 %{SOURCE2} %{buildroot}%{_unitdir}

%post
%{fillup_only -ns security checksig}

%service_add_post YaST2-Second-Stage.service YaST2-Firstboot.service

# bsc#924278 Always enable these services by default, they are already listed
# in systemd-presets-branding package, but that works for new installations
# only, it does not work for upgrades from SLE 11 where scripts had different
# name and were not handled by systemd.
# When we upgrade/update from systemd-based system, scripts are always enabled
# by the service_add_post macro.
systemctl enable YaST2-Second-Stage.service
systemctl enable YaST2-Firstboot.service

%pre
%service_add_pre YaST2-Second-Stage.service YaST2-Firstboot.service

%preun
%service_del_preun YaST2-Second-Stage.service YaST2-Firstboot.service

%postun
%service_del_postun_without_restart YaST2-Second-Stage.service YaST2-Firstboot.service

%files
%license COPYING
%doc %{yast_docdir}
# systemd service files
%{_unitdir}/YaST2-Firstboot.service
%{_unitdir}/YaST2-Second-Stage.service
%{_bindir}/memsample
%{_bindir}/memsample-archive-to-csv
%{_bindir}/memsample-csv-plot
# yupdate script
%{_bindir}/yupdate
%{yast_clientdir}
%{yast_moduledir}
%{yast_desktopdir}
%{_datadir}/autoinstall/
%{yast_schemadir}
%{yast_yncludedir}
%{yast_libdir}
# agents
%{yast_scrconfdir}
# fillup
%{_fillupdir}/sysconfig.security-checksig
# programs and scripts
%{yast_ystartupdir}/startup
# installation hooks
%{yast_vardir}
%{_datadir}/metainfo/org.*yast.*xml
%{_datadir}/icons/hicolor/*/apps/yast-*

%changelog
