"""Models for defining regions to be converted into OME-Zarr format."""

from ome_zarr_converters_tools.models._acquisition import (
    AcquisitionDetails,
)
from ome_zarr_converters_tools.models._tile import BaseTile

__all__ = [
    "AcquisitionDetails",
    "BaseTile",
]
