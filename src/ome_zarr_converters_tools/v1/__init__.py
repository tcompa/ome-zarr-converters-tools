"""This tooling will be removed before v07 release."""

from importlib.metadata import PackageNotFoundError, version

from ome_zarr_converters_tools.v1._microplate_utils import wellid_to_row_column
from ome_zarr_converters_tools.v1._omezarr_plate_writers import initiate_ome_zarr_plates
from ome_zarr_converters_tools.v1._task_common_models import (
    AdvancedComputeOptions,
    ConvertParallelInitArgs,
)
from ome_zarr_converters_tools.v1._task_compute_tools import generic_compute_task
from ome_zarr_converters_tools.v1._task_init_tools import build_parallelization_list
from ome_zarr_converters_tools.v1._tile import OriginDict, Point, Tile, Vector
from ome_zarr_converters_tools.v1._tiled_image import (
    PathBuilder,
    PlatePathBuilder,
    SimplePathBuilder,
    TiledImage,
)

try:
    __version__ = version("ome-zarr-converters-tools")
except PackageNotFoundError:
    __version__ = "uninstalled"
__author__ = "Lorenzo Cerrone"
__email__ = "lorenzo.cerrone@uzh.ch"

__all__ = [
    "AdvancedComputeOptions",
    "ConvertParallelInitArgs",
    "OriginDict",
    "PathBuilder",
    "PlatePathBuilder",
    "Point",
    "SimplePathBuilder",
    "Tile",
    "TiledImage",
    "Vector",
    "build_parallelization_list",
    "generic_compute_task",
    "initiate_ome_zarr_plates",
    "wellid_to_row_column",
]
