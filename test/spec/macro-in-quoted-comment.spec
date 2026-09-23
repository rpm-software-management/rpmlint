Name:           macro-in-quoted-comment
Version:        0
Release:        0
Summary:        macro-in-quoted-comment-no-warning
Patch0:         patch0.patch
License:        GPL-2.0-only
Group:          
URL:            http://rpmlint.zarb.org/#%{name}
Source0:        Source0.tar.gz

%description
There are '#' characters inside shell-quoted strings below. They do not
start comments, so the macros following them must not trigger
macro-in-comment warnings.

%prep
%autosetup

%build

%install
sed -i '/^---/ a #replace default location of "settings.d"\n:settings_directory: %{_sysconfdir}/%{name}/settings.d\n' \
        %{_sysconfdir}/%{name}/settings.yml
echo "double-quoted #hash %{_bindir} is not a comment either"

%files
%{_libdir}/foo

%changelog
