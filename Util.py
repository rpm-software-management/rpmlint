import Pkg
import os.path

def get_default_valid_rpmgroups(filename = ""):
    """ Get the default rpm group from filename, or from rpm package if no
    filename is given"""
    groups = []
    if not filename:
        p = Pkg.InstalledPkg('rpm')
        filename = filter(lambda x: x.endswith('/GROUPS'), p.files().keys())[0]
    if filename and os.path.exists(filename):
        fobj = open(filename)
        try:
            groups = fobj.read().strip().splitlines()
        finally:
            fobj.close()
        if not 'Development/Debug' in groups:
            groups.append('Development/Debug')
            groups.sort()
    return groups
