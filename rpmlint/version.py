try:
    from importlib.metadata import version as implib_metadata_version
except ImportError:
    from importlib_metadata import version as implib_metadata_version

__version__ = implib_metadata_version('rpmlint')
