#############################################################################
# File		: Makefile
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Mon Sep 30 13:20:18 1999
# Version	: $Id$
# Purpose	: rules to manage the files.
#############################################################################

BINDIR=/usr/bin
LIBDIR=/usr/share/rpmlint
ETCDIR=/etc
MANDIR=/usr/share/man

FILES = rpmlint *.py INSTALL README README.devel COPYING tools/*.py \
	Makefile config rpmdiff rpmlint.bash-completion rpmlint.1 \
	test.sh test/*.rpm test/*.spec test/*.py
GENERATED = AUTHORS ChangeLog __version__.py

PACKAGE = rpmlint
PYTHON = python

# update this variable to create a new release
VERSION := 1.1
TAG := $(shell echo "V$(VERSION)" | tr -- '-.' '__')
SVNBASE = $(shell svn info . | grep URL | sed -e 's/[^:]*:\s*//' -e 's,/\(trunk\|tags/.\+\)$$,,')

# for the [A-Z]* part
LC_ALL:=C
export LC_ALL

all: __version__.py __isocodes__.py
	if [ "x${COMPILE_PYC}" = "x1" ] ; then \
		$(PYTHON) -m py_compile [A-Z]*.py __*__.py ; \
	fi
	$(PYTHON) -O -m py_compile [A-Z]*.py __*__.py

clean:
	rm -f *~ *.pyc *.pyo $(GENERATED)

install: all
	mkdir -p $(DESTDIR)$(LIBDIR) $(DESTDIR)$(BINDIR) $(DESTDIR)$(ETCDIR)/$(PACKAGE) $(DESTDIR)$(ETCDIR)/bash_completion.d $(DESTDIR)$(MANDIR)/man1
	-cp -p *.pyc $(DESTDIR)$(LIBDIR)
	cp -p *.py *.pyo $(DESTDIR)$(LIBDIR)
	cp -p rpmlint rpmdiff $(DESTDIR)$(BINDIR)
	cp -p config $(DESTDIR)$(ETCDIR)/$(PACKAGE)
	cp -p rpmlint.bash-completion $(DESTDIR)$(ETCDIR)/bash_completion.d/rpmlint
	cp -p rpmlint.1 $(DESTDIR)$(MANDIR)/man1/rpmlint.1

verify:
	pychecker --limit=100 [A-Z]*.py __*__.py

.PHONY: check

check:
	./test.sh

version:
	@echo "$(VERSION)"


dist: cleandist localcopy tar

cleandist:
	rm -rf $(PACKAGE)-$(VERSION) $(PACKAGE)-$(VERSION).tar.xz

localcopy: $(FILES) $(GENERATED)
	mkdir $(PACKAGE)-$(VERSION)
	cp -p --parents $(FILES) $(GENERATED) $(PACKAGE)-$(VERSION)

tar: localcopy
	tar cv --owner=root --group=root -f $(PACKAGE)-$(VERSION).tar $(PACKAGE)-$(VERSION)
	xz -9evf $(PACKAGE)-$(VERSION).tar
	rm -rf $(PACKAGE)-$(VERSION)

export:
	svn export $(SVNBASE)/tags/$(TAG) $(PACKAGE)-$(VERSION)

tag:
	@if svn list $(SVNBASE)/tags/$(TAG) &>/dev/null ; then \
	    echo "ERROR: tag \"$(TAG)\" probably already exists" ; \
	    exit 1 ; \
	else \
	    echo 'svn copy -m "Tag $(TAG)." . $(SVNBASE)/tags/$(TAG)' ; \
	    svn copy -m "Tag $(TAG)." . $(SVNBASE)/tags/$(TAG) ; \
	fi

AUTHORS: authors.xml authors.xsl
	xsltproc authors.xsl authors.xml | sort -u > $@

ChangeLog: $(FILES) authors.xml
	svn2cl --authors=authors.xml --group-by-day --reparagraph \
		--strip-prefix=trunk

__version__.py: Makefile
	echo "# Automatically generated, do not edit" > $@
	echo "__version__ = '$(VERSION)'" >> $@

__isocodes__.py:
	tools/generate-isocodes.py > $@

# Makefile ends here
