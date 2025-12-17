"""Functions to build TiledImage models from Tile models."""

from typing import Any

from ome_zarr_converters_tools.models._acquisition import (
    FullContextBaseModel,
)
from ome_zarr_converters_tools.models._tile import BaseTile
from ome_zarr_converters_tools.models._tile_region import TiledImage


def tiled_image_from_tiles(
    tiles: list[BaseTile],
    context: FullContextBaseModel,
    resource: Any | None = None,
) -> list[TiledImage]:
    """Create a TiledImage from a dictionary.

    Args:
        tiles: List of Tile models to build the TiledImage from.
        context: Full context model for the conversion.
        resource: Optional resource to pass to image loaders.

    Returns:
        A TiledImage model.

    """
    split_tiles = context.converter_options.tiling_mode == "none"
    tiled_images = {}
    for tile in tiles:
        suffix = "" if not split_tiles else f"_{tile.fov_name}"
        tile.collection.suffix = suffix
        path = tile.collection.path()
        data_type = (
            context.acquisition_details.data_type
            or tile.image_loader.find_data_type(resource)
        )
        attributes = tile.model_extra or {}
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
                attributes=attributes,
            )
        tiled_images[path].add_tile(tile)
    return list(tiled_images.values())
