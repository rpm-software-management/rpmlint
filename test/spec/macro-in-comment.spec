Name:           macro-in-comment
Version:        0
Release:        0
Summary:        macro-in-comment-warning
Patch0:         patch0.patch
License:        GPL-2.0-only
Group:          
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz

%description
There is a unescaped macro after a shell style comment in the specfile.
Macros are expanded everywhere, so check if it can cause a problem in this
case and escape the macro with another leading % if appropriate.

%prep
%autopatch
%autosetup

%build
# this is a comment %{version}

%install

%files
%{_libdir}/foo

%changelog
