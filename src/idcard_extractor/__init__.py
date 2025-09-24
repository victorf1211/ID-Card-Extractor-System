"""ID Card Extractor package."""

from importlib.metadata import version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from importlib.metadata import PackageNotFoundError
else:
    try:
        from importlib.metadata import PackageNotFoundError
    except ImportError:

        class PackageNotFoundError(ImportError):
            pass


try:
    from importlib.metadata import PackageNotFoundError, version

    __version__ = version(__package__)
except PackageNotFoundError:
    __version__ = "0.0.0"
