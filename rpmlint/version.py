try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    from importlib_metadata import version, PackageNotFoundError

try:
    __version__ = version('rpmlint')
except PackageNotFoundError:
    __version__ = '0.0.0'
