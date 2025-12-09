"""Functions to write TiledImage models from Tile models."""

from typing import Any

from ome_zarr_converters_tools.models._acquisition import ConverterOptions
from ome_zarr_converters_tools.models._tile_region import TiledImage
from ome_zarr_converters_tools.utils._allignment import align_regions
from ome_zarr_converters_tools.utils._tiling import tile_regions
from ome_zarr_converters_tools.utils._write_images import write_tiled_image_as_zarr


def tiled_image_from_tiles(
    tiled_image: TiledImage,
    converter_options: ConverterOptions,
    resource: Any | None = None,
) -> dict[str, Any]:
    """Write a TiledImage from a dictionary."""
    aligned_image = align_regions(
        tiled_image, alignement_corrections=converter_options.alignment_correction
    )
    tiled_image = tile_regions(aligned_image, tiling_mode=converter_options.tiling_mode)
    updates = write_tiled_image_as_zarr(
        tiled_image, resource, ome_zarr_options=converter_options.omezarr_options
    )
    return updates
