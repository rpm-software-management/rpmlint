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

FILES = rpmlint *.py INSTALL README README.devel COPYING tools/*.py \
	Makefile config rpmdiff rpmlint.bash-completion rpmlint.1 \
	test.sh test/*.rpm test/*.spec test/*.py
GENERATED = ChangeLog __version__.py

PACKAGE = rpmlint
PYTHON = python

# update this variable to create a new release
VERSION := 1.5

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
	mkdir -p $(DESTDIR)$(LIBDIR) $(DESTDIR)$(BINDIR) $(DESTDIR)$(ETCDIR)/$(PACKAGE) $(DESTDIR)$(MANDIR)/man1
	-cp -p *.pyc $(DESTDIR)$(LIBDIR)
	cp -p *.py *.pyo $(DESTDIR)$(LIBDIR)
	cp -p rpmlint rpmdiff $(DESTDIR)$(BINDIR)
	cp -p config $(DESTDIR)$(ETCDIR)/$(PACKAGE)
	compdir=`pkg-config --variable=completionsdir bash-completion 2>/dev/null` ; \
	if [ "x$$compdir" = "x" ] ; then \
		mkdir -p $(DESTDIR)$(ETCDIR)/bash_completion.d ; \
		cp -p rpmlint.bash-completion $(DESTDIR)$(ETCDIR)/bash_completion.d/rpmlint ; \
	else \
		mkdir -p $(DESTDIR)$$compdir ; \
		cp -p rpmlint.bash-completion $(DESTDIR)$$compdir/rpmlint ; \
		ln -s rpmlint $(DESTDIR)$$compdir/rpmdiff ; \
	fi
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

ChangeLog: $(FILES)
	git2cl > $@

__version__.py: Makefile
	echo "# Automatically generated, do not edit" > $@
	echo "__version__ = '$(VERSION)'" >> $@

__isocodes__.py:
	tools/generate-isocodes.py > $@

# Makefile ends here
