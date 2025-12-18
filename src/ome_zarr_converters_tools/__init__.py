"""This tooling will be removed before v07 release."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ome-zarr-converters-tools")
except PackageNotFoundError:
    __version__ = "uninstalled"
__author__ = "Lorenzo Cerrone"
__email__ = "lorenzo.cerrone@uzh.ch"
