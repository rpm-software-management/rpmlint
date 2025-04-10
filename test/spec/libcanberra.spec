#
# spec file for package libcanberra
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


%define debug_package_requires libcanberra0 = %{version}-%{release}
Name:           libcanberra
Version:        0.30
Release:        0
Summary:        Portable sound event library
License:        LGPL-2.0-or-later
Group:          Development/Libraries/GNOME
URL:            http://0pointer.de/lennart/projects/libcanberra
Source:         http://0pointer.de/lennart/projects/libcanberra/%{name}-%{version}.tar.xz
Source1:        libcanberra-gtk-module.sh
Source99:       baselibs.conf
# PATCH-FIX-UPSTREAM libcanberra-multi-backend.patch boo#753243 fdo#51662 dimstar@opensuse.org -- Set the multi backend as default and allow it actually to work.
Patch0:         libcanberra-multi-backend.patch
# PATCH-FIX-UPSTREAM libcanberra-broadway-fix.patch boo#789066 michael.meeks@suse.com
Patch1:         libcanberra-broadway-fix.patch
BuildRequires:  gtk-doc
BuildRequires:  libltdl-devel
BuildRequires:  pkgconfig
BuildRequires:  update-desktop-files
BuildRequires:  pkgconfig(alsa)
BuildRequires:  pkgconfig(glib-2.0) >= 2.32
BuildRequires:  pkgconfig(gtk+-2.0)
BuildRequires:  pkgconfig(gtk+-3.0)
BuildRequires:  pkgconfig(libpulse) >= 0.9.11
BuildRequires:  pkgconfig(libudev) >= 160
BuildRequires:  pkgconfig(vorbisfile)
BuildRequires:  pkgconfig(x11)

%description
libcanberra is an implementation of the XDG Sound Theme and Name
Specifications, for generating event sounds on free desktops, such
as GNOME. It comes with several backends (ALSA, PulseAudio, null)
and is designed to be portable.

%package -n libcanberra0
Summary:        Portable sound event library
Group:          System/Libraries
Requires:       libpulse0 >= 0.9.11

%description -n libcanberra0
libcanberra is an implementation of the XDG Sound Theme and Name
Specifications, for generating event sounds on free desktops, such
as GNOME. It comes with several backends (ALSA, PulseAudio, null)
and is designed to be portable.

This package contains the main library.

%package        gtk0
Summary:        Portable sound event library -- GTK+ 2 Library
Group:          System/Libraries

%description gtk0
libcanberra is an implementation of the XDG Sound Theme and Name
Specifications, for generating event sounds on free desktops, such
as GNOME. It comes with several backends (ALSA, PulseAudio, null)
and is designed to be portable.

This package contains a library to make it easier to use
libcanberra from GTK+ 2 applications.

%package gtk3-0
Summary:        Portable sound event library -- GTK+ 3 Library
Group:          System/Libraries

%description gtk3-0
libcanberra is an implementation of the XDG Sound Theme and Name
Specifications, for generating event sounds on free desktops, such
as GNOME. It comes with several backends (ALSA, PulseAudio, null)
and is designed to be portable.

This package contains a library to make it easier to use
libcanberra from GTK+ 3 applications.

%package gtk-module-common
Summary:        Portable sound event library -- Common Files for GTK+ Modules
Group:          System/Libraries

%description gtk-module-common
libcanberra is an implementation of the XDG Sound Theme and Name
Specifications, for generating event sounds on free desktops, such
as GNOME. It comes with several backends (ALSA, PulseAudio, null)
and is designed to be portable.

This package contains files common to both the GTK+ 2 and GTK+ 3
modules.

%package gtk2-module
Summary:        Portable sound event library -- GTK+ 2 Module
Group:          System/Libraries
Requires:       %{name}-gtk-module-common = %{version}
Supplements:    (libcanberra0 and gtk2)

%description gtk2-module
libcanberra is an implementation of the XDG Sound Theme and Name
Specifications, for generating event sounds on free desktops, such
as GNOME. It comes with several backends (ALSA, PulseAudio, null)
and is designed to be portable.

This package contains a GTK+ 2 module that triggers input feedback
event sounds.

%package gtk3-module
Summary:        Portable sound event library -- GTK+ 3 Module
Group:          System/Libraries
Requires:       %{name}-gtk-module-common = %{version}
Supplements:    (libcanberra0 and gtk3)

%description gtk3-module
libcanberra is an implementation of the XDG Sound Theme and Name
Specifications, for generating event sounds on free desktops, such
as GNOME. It comes with several backends (ALSA, PulseAudio, null)
and is designed to be portable.

This package contains a GTK+ 3 module that triggers input feedback
event sounds.

%package -n canberra-gtk-play
Summary:        Utilities from libcanberra
Group:          System/GUI/GNOME
Provides:       %{name}-gtk = %{version}
Obsoletes:      %{name}-gtk < %{version}

%description -n canberra-gtk-play
libcanberra is an implementation of the XDG Sound Theme and Name
Specifications, for generating event sounds on free desktops, such
as GNOME. It comes with several backends (ALSA, PulseAudio, null)
and is designed to be portable.

This package provides the canberra-gtk-play utility.

%package -n canberra-gtk-play-gnome
Summary:        .desktop links for the canberra-gtk-play utility
# Disable supplements as we do not want it installed by default.
# This package contains a ready sound for gdm
#Supplements:    gdm
# This package contains login/logout sound for GNOME.
#Supplements:    gnome-session
Group:          System/GUI/GNOME
Provides:       %{name}-gtk-gnome = %{version}
Obsoletes:      %{name}-gtk-gnome < %{version}

%description -n canberra-gtk-play-gnome
libcanberra is an implementation of the XDG Sound Theme and Name
Specifications, for generating event sounds on free desktops, such
as GNOME. It comes with several backends (ALSA, PulseAudio, null)
and is designed to be portable.

This package provides the canberra-gtk-play .desktop files for the
gnome-desktop and gdm.
Currently there are no desktop-login, desktop-logout or
session-ready sounds in the freedesktop sound theme, so installing
this will require a different sound-theme for it to be operational.

%package devel
Summary:        Development files for libcanberra, a portable sound event library
Group:          Development/Libraries/C and C++
Requires:       libcanberra0 = %{version}

%description devel
libcanberra is an implementation of the XDG Sound Theme and Name
Specifications, for generating event sounds on free desktops, such
as GNOME. It comes with several backends (ALSA, PulseAudio, null)
and is designed to be portable.

This package provides the development files for libcanberra.

%package -n libcanberra-gtk3-devel
Summary:        GTK+ 3 development files for libcanberra
Group:          Development/Libraries/C and C++
Requires:       libcanberra-devel
Requires:       libcanberra-gtk3-0 = %{version}
Requires:       libcanberra0 = %{version}

%description -n libcanberra-gtk3-devel
libcanberra is an implementation of the XDG Sound Theme and Name
Specifications, for generating event sounds on free desktops, such
as GNOME. It comes with several backends (ALSA, PulseAudio, null)
and is designed to be portable.

This package provides the development files for libcanberra-gtk3.

%package -n libcanberra-gtk-devel
Summary:        GTK+ 2 development files for libcanberra
Group:          Development/Libraries/C and C++
Requires:       libcanberra-devel
Requires:       libcanberra-gtk0 = %{version}
Requires:       libcanberra0 = %{version}

%description -n libcanberra-gtk-devel
libcanberra is an implementation of the XDG Sound Theme and Name
Specifications, for generating event sounds on free desktops, such
as GNOME. It comes with several backends (ALSA, PulseAudio, null)
and is designed to be portable.

This package provides the development files for libcanberra-gtk2.

%prep
%autosetup -p1
cp %{SOURCE1} libcanberra-gtk-module.sh

%build
%configure \
  --disable-static   \
  --enable-pulse     \
  --enable-alsa      \
  --enable-null      \
  --disable-oss      \
  --enable-udev      \
  --with-builtin=dso
make %{?_smp_mflags} V=1

%install
%make_install
install -Dpm 0755 libcanberra-gtk-module.sh \
  %{buildroot}%{_sysconfdir}/X11/xinit/xinitrc.d/libcanberra-gtk-module.sh
rm %{buildroot}%{_datadir}/doc/libcanberra/README

%suse_update_desktop_file %{buildroot}%{_datadir}/gnome/autostart/libcanberra-login-sound.desktop
%suse_update_desktop_file %{buildroot}%{_datadir}/gdm/autostart/LoginWindow/libcanberra-ready-sound.desktop

find %{buildroot} -type f -name "*.la" -delete -print

%post -n libcanberra0 -p /sbin/ldconfig
%postun -n libcanberra0 -p /sbin/ldconfig
%post gtk0 -p /sbin/ldconfig
%postun gtk0 -p /sbin/ldconfig
%post gtk3-0 -p /sbin/ldconfig
%postun gtk3-0 -p /sbin/ldconfig

%files -n libcanberra0
%doc README
%license LGPL
%{_libdir}/libcanberra.so.*
%dir %{_libdir}/libcanberra-%{version}/
%{_libdir}/libcanberra-%{version}/libcanberra-alsa.so
%{_libdir}/libcanberra-%{version}/libcanberra-multi.so
%{_libdir}/libcanberra-%{version}/libcanberra-null.so
%{_libdir}/libcanberra-%{version}/libcanberra-pulse.so

%files gtk0
%{_libdir}/libcanberra-gtk.so.*

%files gtk3-0
%{_libdir}/libcanberra-gtk3.so.*

%files gtk-module-common
%{_bindir}/canberra-boot
%dir %{_sysconfdir}/X11/xinit/
%dir %{_sysconfdir}/X11/xinit/xinitrc.d/
%{_sysconfdir}/X11/xinit/xinitrc.d/libcanberra-gtk-module.sh
%dir %{_libdir}/gnome-settings-daemon-3.0/
%dir %{_libdir}/gnome-settings-daemon-3.0/gtk-modules/
%{_libdir}/gnome-settings-daemon-3.0/gtk-modules/canberra-gtk-module.desktop

%files gtk2-module
%{_libdir}/gtk-2.0/modules/libcanberra-gtk-module.so

%files gtk3-module
%{_libdir}/gtk-3.0/modules/libcanberra-gtk*-module.so

%files -n canberra-gtk-play
%{_bindir}/canberra-gtk-play

%files -n canberra-gtk-play-gnome
%dir %{_datadir}/gnome/
%dir %{_datadir}/gnome/autostart/
%{_datadir}/gnome/autostart/libcanberra-login-sound.desktop
%dir %{_datadir}/gnome/shutdown/
%{_datadir}/gnome/shutdown/libcanberra-logout-sound.sh
%dir %{_datadir}/gdm/
%dir %{_datadir}/gdm/autostart/
%dir %{_datadir}/gdm/autostart/LoginWindow/
%{_datadir}/gdm/autostart/LoginWindow/libcanberra-ready-sound.desktop

%files -n libcanberra-gtk-devel
%{_libdir}/libcanberra-gtk.so
%{_libdir}/pkgconfig/libcanberra-gtk.pc

%files -n libcanberra-gtk3-devel
%{_libdir}/libcanberra-gtk3.so
%{_libdir}/pkgconfig/libcanberra-gtk3.pc

%files devel
%doc %{_datadir}/gtk-doc/html/libcanberra/
%{_includedir}/canberra.h
%{_includedir}/canberra-gtk.h
%{_libdir}/libcanberra.so
%{_libdir}/pkgconfig/libcanberra.pc
%dir %{_datadir}/vala/
%dir %{_datadir}/vala/vapi/
%{_datadir}/vala/vapi/*.vapi

%changelog
