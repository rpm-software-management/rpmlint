#############################################################################
# File		: Makefile
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Mon Sep 30 13:20:18 1999
# Purpose	: rules to manage the files.
#############################################################################

BINDIR=/usr/bin
LIBDIR=/usr/share/rpmlint
ETCDIR=/etc
MANDIR=/usr/share/man

FILES = rpmlint *.py INSTALL README.md README.devel COPYING tools/*.py \
	Makefile config rpmdiff rpmdiff.1 rpmlint.bash-completion rpmlint.1 \
	test.sh test/*/*.rpm test/spec/*.spec test/*.py
GENERATED = __version__.py

PACKAGE = rpmlint
PYTHON = /usr/bin/python

# update this variable to create a new release
VERSION := 1.10

all: __version__.py __isocodes__.py

clean:
	rm -rf *~ *.py[co] */*.py[co] __pycache__ */__pycache__ $(GENERATED)

install: all
	mkdir -p $(DESTDIR)$(LIBDIR) $(DESTDIR)$(BINDIR) $(DESTDIR)$(ETCDIR)/$(PACKAGE) $(DESTDIR)$(MANDIR)/man1
	cp -p *.py $(DESTDIR)$(LIBDIR)
	if [ "x${COMPILE_PYC}" = "x1" ] ; then \
		$(PYTHON) -m py_compile \
			$(DESTDIR)$(LIBDIR)/[A-Z]*.py \
			$(DESTDIR)$(LIBDIR)/__*__.py ; \
	fi
	$(PYTHON) -O -m compileall -d $(LIBDIR) $(DESTDIR)$(LIBDIR)
	for file in rpmlint rpmdiff ; do \
		sed -e "s,#!/usr/bin/python ,#!$(PYTHON) ," $$file > $(DESTDIR)$(BINDIR)/$$file ; \
		chmod +x $(DESTDIR)$(BINDIR)/$$file ; \
	done
	cp -p config $(DESTDIR)$(ETCDIR)/$(PACKAGE)
	compdir=`pkg-config --variable=completionsdir bash-completion 2>/dev/null` ; \
	if [ "x$$compdir" = "x" ] ; then \
		mkdir -p $(DESTDIR)$(ETCDIR)/bash_completion.d ; \
		cp -p rpmlint.bash-completion $(DESTDIR)$(ETCDIR)/bash_completion.d/rpmlint ; \
	else \
		mkdir -p $(DESTDIR)$$compdir ; \
		cp -p rpmlint.bash-completion $(DESTDIR)$$compdir/rpmlint ; \
		ln -sf rpmlint $(DESTDIR)$$compdir/rpmdiff ; \
	fi
	cp -p rpmdiff.1 rpmlint.1 $(DESTDIR)$(MANDIR)/man1

verify:
	pychecker --limit=100 [A-Z]*.py __*__.py

check:
	./test.sh

__version__.py: Makefile
	echo "# Automatically generated, do not edit" > $@
	echo "__version__ = '$(VERSION)'" >> $@

__isocodes__.py:
	tools/generate-isocodes.py > $@

.PHONY: all clean install verify check

# Makefile ends here
