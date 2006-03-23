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
ETCDIR=/etc/rpmlint
MANDIR=/usr/share/man

FILES= rpmlint *.py AUTHORS INSTALL README README.devel COPYING ChangeLog Makefile \
       config rpmlint.spec rpmdiff rpmlint.bash-completion rpmlint.1

PACKAGE=rpmlint
VERSION:=$(shell rpm -q --qf %{VERSION} --specfile $(PACKAGE).spec)
RELEASE:=$(shell rpm -q --qf %{RELEASE} --specfile $(PACKAGE).spec)
TAG := $(shell echo "V$(VERSION)_$(RELEASE)" | tr -- '-.' '__')

# for the [A-Z]* part 
LC_ALL:=C
export LC_ALL

RPMOPT = --clean --rmspec

all:
	./compile.py "$(LIBDIR)/" [A-Z]*.py
	@for f in [A-Z]*.py; do if grep -q '^[^#]*print ' $$f; then echo "print statement in $$f:"; grep -Hn '^[^#]*print ' $$f; exit 1; fi; done

clean:
	rm -f *~ *.pyc *.pyo ChangeLog

install:
	-mkdir -p $(DESTDIR)$(LIBDIR) $(DESTDIR)$(BINDIR) $(DESTDIR)$(ETCDIR) $(DESTDIR)$(ETCDIR)/bash_completion.d $(DESTDIR)$(MANDIR)/man1
	cp -p *.py *.pyo $(DESTDIR)$(LIBDIR)
	rm -f $(DESTDIR)$(LIBDIR)/compile.py*
	if [ -z "$(POLICY)" ]; then \
	  sed -e 's/@VERSION@/$(VERSION)/' < rpmlint.py > $(DESTDIR)$(LIBDIR)/rpmlint.py ; \
	else \
	  sed -e 's/@VERSION@/$(VERSION)/' -e 's/policy=None/policy="$(POLICY)"/' < rpmlint.py > $(DESTDIR)$(LIBDIR)/rpmlint.py; \
	fi
	cp -p rpmlint rpmdiff $(DESTDIR)$(BINDIR)
	cp -p config  $(DESTDIR)$(ETCDIR)
	cp -p rpmlint.bash-completion  $(DESTDIR)$(ETCDIR)/bash_completion.d/rpmlint
	cp -p rpmlint.1 $(DESTDIR)$(MANDIR)/man1/rpmlint.1

verify:
	pychecker *.py

version:
	@echo "$(VERSION)-$(RELEASE)"

# rules to build a test rpm

localrpm: localdist buildrpm

localdist: cleandist dir localcopy tar

cleandist:
	rm -rf $(PACKAGE)-$(VERSION) $(PACKAGE)-$(VERSION).tar.bz2

dir:
	mkdir $(PACKAGE)-$(VERSION)

localcopy:
	tar c $(FILES) | tar x -C $(PACKAGE)-$(VERSION)

tar: changelog
	tar cvf $(PACKAGE)-$(VERSION).tar $(PACKAGE)-$(VERSION)
	bzip2 -9vf $(PACKAGE)-$(VERSION).tar
	rm -rf $(PACKAGE)-$(VERSION)

buildrpm:
	rpm -ta $(RPMOPT) $(PACKAGE)-$(VERSION).tar.bz2

# rules to build a distributable rpm

rpm: changelog cvstag dist buildrpm

dist: cleandist dir export tar

export:
	cvs export -d $(PACKAGE)-$(VERSION) -r $(TAG) $(PACKAGE)

cvstag:
	cvs tag $(CVSTAGOPT) $(TAG)

changelog:
	svn2cl --authors=authors.xml

# Makefile ends here
