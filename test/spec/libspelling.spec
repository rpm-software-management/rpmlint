#
# spec file for package libspelling
#
# Copyright (c) 2025 SUSE LLC
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


%define so_ver 1-2
%define api_ver 1

Name:           libspelling
Version:        0.4.6
Release:        0
Summary:        A spellcheck library for GTK 4
License:        LGPL-2.1-or-later
URL:            https://gitlab.gnome.org/chergert/libspelling
Source:         %{name}-%{version}.tar.zst
Patch:          dummy.patch

BuildRequires:  c_compiler
BuildRequires:  meson
BuildRequires:  pkgconfig
BuildRequires:  pkgconfig(enchant-2)
BuildRequires:  pkgconfig(gi-docgen)
BuildRequires:  pkgconfig(gio-2.0)
BuildRequires:  pkgconfig(gobject-introspection-1.0)
BuildRequires:  pkgconfig(gtk4) >= 4.15.5
BuildRequires:  pkgconfig(gtksourceview-5)
BuildRequires:  pkgconfig(icu-uc)
BuildRequires:  pkgconfig(vapigen)
# For tests
BuildRequires:  myspell-en_US

BuildSystem:    meson
BuildOption:    -Dsysprof=false

%description
A spellcheck library for GTK 4.
This library is heavily based upon GNOME Text Editor and GNOME
Builder's spellcheck implementation. However, it is licensed
LGPL-2.1-or-later

%package -n libspelling%{so_ver}
Summary:        Shared libraries for %{name}
Provides:       %{name} = %{version}

%description -n libspelling%{so_ver}
Shared libraries for %{name}.

%package -n typelib-1_0-Spelling-%{api_ver}
Summary:        Introspection file for %{name}

%description -n typelib-1_0-Spelling-1
Introspection file for %{name}.

%package devel
Summary:        Development files for %{name}
Requires:       libspelling%{so_ver} = %{version}
Requires:       typelib-1_0-Spelling-%{api_ver} = %{version}

%description devel
The %{name}-devel package contains libraries and header files for
developing applications that use %{name}.

%lang_package

%install -a
%find_lang %{name} %{?no_lang_C}

%ldconfig_scriptlets -n libspelling%{so_ver}

%files -n libspelling%{so_ver}
%license COPYING
%doc NEWS README.md
%{_libdir}/libspelling-%{api_ver}.so.*

%files -n typelib-1_0-Spelling-%{api_ver}
%{_libdir}/girepository-1.0/Spelling-%{api_ver}.typelib

%files devel
%doc %{_datadir}/doc/libspelling-%{api_ver}/
%{_includedir}/libspelling-%{api_ver}
%{_libdir}/libspelling-%{api_ver}.so
%{_libdir}/pkgconfig/libspelling-%{api_ver}.pc
%{_datadir}/gir-1.0/Spelling-%{api_ver}.gir
%dir %{_datadir}/vala
%dir %{_datadir}/vala/vapi
%{_datadir}/vala/vapi/libspelling-%{api_ver}.deps
%{_datadir}/vala/vapi/libspelling-%{api_ver}.vapi

%files lang -f %{name}.lang

%changelog
