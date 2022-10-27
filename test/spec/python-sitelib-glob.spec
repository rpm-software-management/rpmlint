#
# spec file for package python-sitelib-glob
#
# Copyright (c) specCURRENT_YEAR SUSE LINUX GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#


Name:           python-sitelib-glob
Version:        0.1
Release:        0
Summary:        Cool Python package
License:        GPL-2.0-or-later
# FIXME: use correct group, see "https://en.opensuse.org/openSUSE:Package_group_guidelines"
Group:          Development/Libraries/Python
Url:            http://rpmlint.zarb.org/#%{name}
BuildRequires:  python-rpm-macros
%{python_subpackages}

%description
Cool Python Package

%prep
%autosetup -p1

%build
%python_build

%install
%python_install

%files %{python_files}
%{python_sitelib}/*

%changelog

