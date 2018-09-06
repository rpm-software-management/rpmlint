FROM fedora:rawhide

# --nogpgcheck: Ignore transient(?) package signature failures
RUN dnf --nogpgcheck -y install \
        /usr/bin/appstream-util \
        /usr/bin/cpio \
        /usr/bin/bzip2 \
        /usr/bin/desktop-file-validate \
        /usr/bin/groff \
        /usr/bin/gtbl \
        /usr/bin/make \
        /usr/bin/man \
        /usr/bin/perl \
        /usr/bin/python3 \
        /usr/bin/readelf \
        /usr/bin/xz \
        hunspell-en \
        hunspell-cs \
        python3-setuptools \
        python3-enchant \
        python3-magic \
        python3-rpm \
        python3-pytest \
        python3-pytest-cov \
        python3-pytest-runner \
        python3-flake8 \
        python3-flake8-import-order \
        python3-pyxdg \
        python3-configobj \
        rpm-build

WORKDIR /usr/src/rpmlint
COPY . .
