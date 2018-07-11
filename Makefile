all: rpmlint/__isocodes__.py

clean:
	rm -f rpmlint/__isocodes__.py

rpmlint/__isocodes__.py:
	tools/generate-isocodes.py > $@
