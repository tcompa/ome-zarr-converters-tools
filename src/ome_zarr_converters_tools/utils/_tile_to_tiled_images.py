"""Functions to build TiledImage models from Tile models."""

from typing import Any

from ome_zarr_converters_tools.filters._filter_pipeline import (
    FilterStep,
    apply_filter_pipeline,
)
from ome_zarr_converters_tools.models._acquisition import (
    FullContextBaseModel,
)
from ome_zarr_converters_tools.models._tile import BaseTile
from ome_zarr_converters_tools.models._tile_region import TiledImage


def tiled_image_from_tiles(
    tiles: list[BaseTile],
    context: FullContextBaseModel,
    filters: list[FilterStep] | None = None,
    resource: Any | None = None,
) -> list[TiledImage]:
    """Create a TiledImage from a dictionary.

    Args:
        tiles: List of Tile models to build the TiledImage from.
        context: Full context model for the conversion.
        filters: Optional list of filter steps to apply to the tiles before
            building the TiledImage.
        resource: Optional resource to pass to image loaders.

    Returns:
        A TiledImage model.

    """
    split_tiles = context.converter_options.tiling_mode == "none"
    if filters is not None:
        tiles = apply_filter_pipeline(tiles, filters_config=filters)
    tiled_images = {}
    for tile in tiles:
        suffix = "" if not split_tiles else f"_{tile.fov_name}"
        path = tile.collection.path(suffix=suffix)
        data_type = (
            context.acquisition_details.data_type
            or tile.image_loader.find_data_type(resource)
        )
        if path not in tiled_images:
            tiled_images[path] = TiledImage(
                path=path,
                regions=[],
                data_type=data_type,
                channel_names=tile.channel_names,
                wavelengths=tile.wavelengths,
                pixelsize=tile.pixelsize,
                z_spacing=tile.z_spacing,
                t_spacing=tile.t_spacing,
                axes=tile.axes,
                collection=tile.collection,
            )
        tiled_images[path].add_tile(tile)
    return list(tiled_images.values())
