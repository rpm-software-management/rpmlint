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

FILES= rpmlint *.py INSTALL README COPYING ChangeLog Makefile config

all:
	./compile.py [A-Z]*.py

clean:
	rm -f *~ *.pyc *.pyo

install:
	-mkdir -p $(DESTDIR)$(LIBDIR) $(DESTDIR)$(BINDIR) $(DESTDIR)$(ETCDIR)
	cp -p rpmlint.py *.pyo $(DESTDIR)$(LIBDIR)
	cp -p rpmlint $(DESTDIR)$(BINDIR)
	cp -p config  $(DESTDIR)$(ETCDIR)

dist:
	VERSION=`python rpmlint.py -V|sed -e 's/rpmlint version //' -e 's/ Copyright (C) 1999 Frederic Lepied//'`; \
	rm -f rpmlint-$$VERSION.tar.bz2; \
	mkdir rpmlint-$$VERSION; \
	ln $(FILES) rpmlint-$$VERSION/; \
	tar cvf rpmlint-$$VERSION.tar rpmlint-$$VERSION;\
	bzip2 -9vf rpmlint-$$VERSION.tar;\
	rm -rf rpmlint-$$VERSION

ndist:
	TEMP=$$$$;\
	rm -f rpmlint.tar.bz2; \
	mkdir -p $$TEMP/rpmlint; \
	ln $(FILES) $$TEMP/rpmlint/; \
	tar cvf rpmlint.tar -C $$TEMP rpmlint;\
	bzip2 -9vf rpmlint.tar;\
	rm -rf $$TEMP

# Makefile ends here
