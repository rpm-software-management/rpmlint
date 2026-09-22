#!/bin/sh
# Regenerate the small ELF fixtures used by test_binaries.py via
# get_tested_mock_package(..., {'content-path': ...}).
#
# The binaries are built for x86-64; tests that depend on x86-64 specifics
# are skipped elsewhere, the rest only need parseable ELF metadata.
set -eu
cd "$(dirname "$0")"

cat > main.c <<'EOF'
int main(void)
{
    return 0;
}
EOF

cat > shlib.c <<'EOF'
int rpmlint_test_function(void)
{
    return 42;
}
EOF

# undefined SSL symbol on purpose, used by the crypto-policy tests
cat > ssluser.c <<'EOF'
extern int SSL_CTX_set_cipher_list(void *, const char *);
int main(void)
{
    return SSL_CTX_set_cipher_list(0, "DEFAULT");
}
EOF

# stub provider for the symbol above so the executable keeps an UND entry
cat > sslstub.c <<'EOF'
int SSL_CTX_set_cipher_list(void *ctx, const char *list)
{
    (void)ctx;
    (void)list;
    return 0;
}
EOF

# undefined gnutls symbol on purpose, with and without the SYSLOG waiver
# string, used by the crypto-policy waiver tests
cat > gnutlsuser.c <<'EOF'
extern int gnutls_priority_init(void *, const char *);
int main(void)
{
    return gnutls_priority_init(0, "NORMAL");
}
EOF

cat > gnutlswaiveduser.c <<'EOF'
extern int gnutls_priority_init(void *, const char *);
int main(void)
{
    return gnutls_priority_init(0, "SYSLOG");
}
EOF

# stub provider for the symbol above so the executables keep an UND entry
cat > gnutlsstub.c <<'EOF'
int gnutls_priority_init(void *a, const char *b)
{
    (void)a;
    (void)b;
    return 0;
}
EOF

# must reference setgid+setuid (without setgroups), mktemp and gethostbyname
cat > multierror.c <<'EOF'
#include <stdlib.h>
#include <unistd.h>
#include <netdb.h>
int main(void)
{
    char template[] = "/tmp/rpmlint-test-XXXXXX";
    char *name = mktemp(template);
    setgid(0);
    setuid(0);
    struct hostent *he = gethostbyname("localhost");
    return name == 0 || he == 0;
}
EOF

# object with no .text section but a GHC comment, exercising the
# GHC exception in the lto-no-text-in-archive check
cat > ghc.s <<'EOF'
	.file	"ghc.c"
	.ident	"GHC 8.6.5"
EOF

# object with no .text section at all (pure LTO-bytecode stand-in)
: > empty.c

# plain PIE executable without any interesting symbols
gcc -o plain-pie main.c

# executable referencing SSL_CTX_set_cipher_list (kept as UND via the stub lib)
gcc -shared -o libsslstub.so sslstub.c
gcc -o ssl-caller ssluser.c -L. -lsslstub
# shared library referencing SSL_CTX_set_cipher_list (FUNC UND via stub link)
gcc -shared -o ssl-caller.so ssluser.c -L. -lsslstub

# executables referencing gnutls_priority_init (kept as UND via the stub
# lib), one containing the SYSLOG waiver string and one without it
gcc -shared -o libgnutlsstub.so gnutlsstub.c
gcc -o gnutls-caller gnutlsuser.c -L. -lgnutlsstub
gcc -o gnutls-waived-caller gnutlswaiveduser.c -L. -lgnutlsstub

# non-PIE executables
gcc -no-pie -o nonpie-exec main.c
gcc -no-pie -o nonpie-stripped main.c
strip nonpie-stripped

# shared libraries
gcc -shared -o exec-shlib.so shlib.c
gcc -shared -o no-soname.so shlib.c
gcc -shared -Wl,--hash-style=both -Wl,-soname,libpthread.so.0 \
    -o nonexec-shlib.so shlib.c
gcc -shared -Wl,-soname,libtest.so.1x -o invalid-soname.so shlib.c
gcc -shared -Wl,-soname,libtest.so.1 -o policy-soname.so shlib.c
gcc -shared -Wl,-soname,libtest.so.3 -o ldconfig-soname.so shlib.c
gcc -shared -Wl,-soname,libtest.so.4 -o ldconfig-ok.so shlib.c

# static archives
gcc -c -o empty.o empty.c
ar rcs lto-no-text.a empty.o
gcc -c -o with-text.o main.c
ar rcs lto-with-text.a with-text.o
gcc -c -o ghc.o ghc.s
ar rcs ghc-no-text.a ghc.o
gcc -fpatchable-function-entry=2 -c -o patchable.o shlib.c
ar rcs patchable.a patchable.o

# binary calling mktemp/setuid/gethostbyname, stripped like the original
gcc -o multi-error multierror.c 2>/dev/null
strip multi-error

# libtool wrapper shell script
printf '#!/bin/bash\n# This wrapper script should never be moved out of the build directory.\n' \
    > libtool-wrapper.sh

rm -f main.c shlib.c ssluser.c sslstub.c gnutlsuser.c gnutlswaiveduser.c \
      gnutlsstub.c multierror.c ghc.s empty.c \
      libsslstub.so libgnutlsstub.so empty.o with-text.o ghc.o patchable.o
ls -la
