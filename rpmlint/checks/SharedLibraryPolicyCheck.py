import os
import re
import rpm
import stat

from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.checks.BinariesCheck import BinaryInfo
from rpmlint import Pkg


_essential_dependencies = (
    'ld-linux.so.2',
    'libacl.so.1',
    'libanl.so.1',
    'libanonymous.so.2',
    'libattr.so.1',
    'libaudit.so.0',
    'libauparse.so.0',
    'libBrokenLocale.so.1',
    'libbz2.so.1',
    'libcidn.so.1',
    'libck-connector.so.0',
    'libcom_err.so.2',
    'libcrack.so.2',
    'libcrypto.so.0.9.8',
    'libcrypt.so.1',
    'libc.so.6',
    'libdbus-1.so.3',
    'libdbus-glib-1.so.2',
    'libdes425.so.3',
    'libdl.so.2',
    'libexpat.so.1',
    'libform.so.5',
    'libformw.so.5',
    'libgcc_s.so.1',
    'libgcrypt.so.11',
    'libgdbm_compat.so.3',
    'libgdbm.so.3',
    'libgfortran3',
    'libgio-2.0.so.0',
    'libglib-2.0.so.0',
    'libgmodule-2.0.so.0',
    'libgobject-2.0.so.0',
    'libgpg-error.so.0',
    'libgssapi_krb5.so.2',
    'libgssrpc.so.4',
    'libgthread-2.0.so.0',
    'libhal.so.1',
    'libhal-storage.so.1',
    'libhd.so.14',
    'libhistory.so.5',
    'libk5crypto.so.3',
    'libkadm5clnt.so.5',
    'libkadm5srv.so.5',
    'libkdb5.so.4',
    'libkeyutils.so.1',
    'libkrb4.so.2',
    'libkrb5.so.3',
    'libkrb5support.so.0',
    'libksba.so.8',
    'liblber-2.4.so.2',
    'libldap-2.4.so.2',
    'libldap_r-2.4.so.2',
    'liblogin.so.2',
    'liblog_syslog.so.1',
    'libltdl.so.3',
    'libmagic.so.1',
    'libmenu.so.5',
    'libmenuw.so.5',
    'libm.so.6',
    'libncurses.so.5',
    'libncursesw.so.5',
    'libnscd.so.1',
    'libnsl.so.1',
    'libnss_compat.so.2',
    'libnss_dns.so.2',
    'libnss_files.so.2',
    'libnss_hesiod.so.2',
    'libnss_nisplus.so.2',
    'libnss_nis.so.2',
    'libopenct.so.1',
    'libopensc.so.2',
    'libpamc.so.0',
    'libpam_misc.so.0',
    'libpam.so.0',
    'libpanel.so.5',
    'libpanelw.so.5',
    'libparted-1.8.so.8',
    'libpcrecpp.so.0',
    'libpcreposix.so.0',
    'libpcre.so.0',
    'libpcsclite.so.1',
    'libpkcs15init.so.2',
    'libpolkit-dbus.so.2',
    'libpolkit-grant.so.2',
    'libpolkit.so.2',
    'libpopt.so.0',
    'libpthread.so.0',
    'libpth.so.20',
    'libreadline.so.5',
    'libresmgr.so.0.9.8',
    'libresmgr.so.1',
    'libresolv.so.2',
    'librt.so.1',
    'libsasl2.so.2',
    'libsasldb.so.2',
    'libscconf.so.2',
    'libslp.so.1',
    'libsmbios.so.1',
    'libssl.so.0.9.8',
    'libss.so.2',
    'libstdc++.so.6',
    'libthread_db.so.1',
    'libtic.so.5',
    'libusb-0.1.so.4',
    'libusbpp-0.1.so.4',
    'libutil.so.1',
    'libuuid.so.1',
    'libvolume_id.so.0',
    'libwrap.so.0',
    'libX11.so.6',
    'libX11-xcb.so.1',
    'libXau.so.6',
    'libxcb-composite.so.0',
    'libxcb-damage.so.0',
    'libxcb-dpms.so.0',
    'libxcb-glx.so.0',
    'libxcb-randr.so.0',
    'libxcb-record.so.0',
    'libxcb-render.so.0',
    'libxcb-res.so.0',
    'libxcb-screensaver.so.0',
    'libxcb-shape.so.0',
    'libxcb-shm.so.0',
    'libxcb.so.1',
    'libxcb-sync.so.0',
    'libxcb-xevie.so.0',
    'libxcb-xf86dri.so.0',
    'libxcb-xfixes.so.0',
    'libxcb-xinerama.so.0',
    'libxcb-xlib.so.0',
    'libxcb-xprint.so.0',
    'libxcb-xtest.so.0',
    'libxcb-xvmc.so.0',
    'libxcb-xv.so.0',
    'libxcrypt.so.1',
    'libzio.so.0',
    'libz.so.1',
)


def libname_from_soname(soname):
    libname = str.split(soname, '.so.')
    if len(libname) == 2:
        if libname[0][-1:].isdigit():
            libname = '-'.join(libname)
        else:
            libname = ''.join(libname)
    else:
        libname = soname[:-3]
    libname = libname.replace('.', '_')
    return libname


class LibraryPolicyCheck(AbstractCheck.AbstractCheck):
    """
    Verify shared library packaging policy rules

    This package validates the shared libraries naming scheme based
    on the Debian/openSUSE shared libraries policy:
     https://en.opensuse.org/openSUSE:Shared_library_packaging_policy
     https://www.debian.org/doc/debian-policy/ch-sharedlibs.html
    """
    strongly_versioned_re = re.compile(r'-[\d\.]+\.so$')

    def check(self, pkg):
        if pkg.is_source:
            return

        # check if the package contains any library

        # Only check unsuffixed lib* packages
        if pkg.name.endswith('-devel') or pkg.name.endswith('-doc'):
            return

        files = pkg.files()

        # Search for shared libraries in this package
        libs = set()
        libs_needed = set()
        libs_to_dir = dict()
        dirs = set()
        reqlibs = set()
        pkg_requires = set(map(lambda x: str.split(x[0], '(')[0],
                               pkg.requires()))

        for f, pkgfile in files.items():
            if '.so.' in f or f.endswith('.so'):
                filename = pkg.dirName() + '/' + f
                if stat.S_ISREG(files[f].mode) and pkgfile.magic.startswith('ELF '):
                    bi = BinaryInfo(pkg, filename, f, False, True)
                    libs_needed = libs_needed.union(bi.needed)
                    if bi.soname != 0:
                        lib_dir = '/'.join(f.split('/')[:-1])
                        libs.add(bi.soname)
                        libs_to_dir[bi.soname] = lib_dir
                        dirs.add(lib_dir)
                    if bi.soname in pkg_requires:
                        # But not if the library is used by the pkg itself
                        # This avoids program packages with their own
                        # private lib
                        # FIXME: we'd need to check if somebody else links
                        # to this lib
                        reqlibs.add(bi.soname)

        std_dirs = dirs.intersection((
            '/lib', '/lib64', '/usr/lib', '/usr/lib64'))

        # If this is a program package (all libs it provides are
        # required by itself), bail out
        if not pkg.name.startswith('lib') and len(libs.difference(reqlibs)) == 0:
            return

        std_lib_package = False
        if pkg.name.startswith('lib') and pkg.name[-1].isdigit():
            std_lib_package = True

        # ignore libs in a versioned non_std_dir
        if std_lib_package:
            for lib in libs.copy():
                lib_dir = libs_to_dir[lib]
                if lib_dir.startswith('/opt/kde3'):
                    continue
                for lib_part in lib_dir.split('/'):
                    if len(lib_part) == 0:
                        continue
                    if lib_part[-1].isdigit() and not lib_part.endswith('lib64'):
                        libs.remove(lib)
                        break

        # Check for non-versioned libs in a std lib package
        if std_lib_package:
            for lib in libs.copy():
                if (not (lib[-1].isdigit() or
                         self.strongly_versioned_re.search(lib))):
                    self.output.add_info('W', pkg, 'shlib-unversioned-lib', lib)

        # If this package should be or should be splitted into shlib
        # package(s)
        if len(libs) > 0 and len(std_dirs) > 0:
            # If the package contains a single shlib, name after soname
            if len(libs) == 1:
                soname = libs.copy().pop()
                libname = libname_from_soname(soname)
                if libname.startswith('lib') and pkg.name != libname and \
                        pkg.name != libname + '-mini':
                    self.output.add_info('E', pkg, 'shlib-policy-name-error', libname)

            elif not pkg.name[-1:].isdigit():
                self.output.add_info('E', pkg, 'shlib-policy-missing-suffix')

        if (not pkg.name.startswith('lib')) or pkg.name.endswith('-lang'):
            return

        if not libs:
            self.output.add_info('E', pkg, 'shlib-policy-missing-lib')

        # Verify no non-lib stuff is in the package
        dirs = set()
        for f in files:
            if os.path.isdir(pkg.dirName() + f):
                dirs.add(f)

        # Verify shared lib policy package doesn't have hard dependency on non-lib packages
        if std_lib_package:
            for dep in pkg.requires():
                if (dep[0].startswith('rpmlib(') or dep[0].startswith('config(')):
                    continue
                if (dep[1] & (rpm.RPMSENSE_GREATER | rpm.RPMSENSE_EQUAL)) == rpm.RPMSENSE_EQUAL:
                    self.output.add_info('W', pkg, 'shlib-fixed-dependency', Pkg.formatRequire(dep[0], dep[1], dep[2]))

        # Verify non-lib stuff does not add dependencies
        if libs:
            for dep in pkg_requires.difference(_essential_dependencies):
                if '.so.' in dep and dep not in libs and dep not in libs_needed:
                    self.output.add_info('E', pkg, 'shlib-policy-excessive-dependency', dep)

        # Check for non-versioned directories beyond sysdirs in package
        sysdirs = ('/lib', '/lib64', '/usr/lib', '/usr/lib64',
                   '/usr/share', '/usr/share/licenses',
                   '/usr/share/doc/packages')
        cdirs = set()
        for sysdir in sysdirs:
            done = set()
            for dir in dirs:
                if dir.startswith(sysdir + '/'):
                    ssdir = str.split(dir[len(sysdir) + 1:], '/')[0]
                    if not ssdir[-1].isdigit():
                        cdirs.add(sysdir + '/' + ssdir)
                    done.add(dir)
            dirs = dirs.difference(done)
        map(lambda dir: self.output.add_info('E', pkg, 'shlib-policy-nonversioned-dir', dir), cdirs)
