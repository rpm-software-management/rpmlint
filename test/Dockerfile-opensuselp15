FROM opensuse/leap:15

RUN zypper -n install \
        cpio gzip bzip2 groff make elfutils xz \
        perl binutils desktop-file-utils \
        man appstream-glib \
        myspell-en_US myspell-cs_CZ \
        python3-magic \
        python3-pyenchant \
        python3-rpm \
        python3-base \
        python3-setuptools \
        python3-pytest \
        python3-pytest-runner \
        python3-pytest-cov \
        python3-pytest \
        python3-flake8 \
        python3-pyxdg \
        python3-configobj

WORKDIR /usr/src/rpmlint
COPY . .
