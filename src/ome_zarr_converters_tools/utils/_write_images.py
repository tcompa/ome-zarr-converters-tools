from typing import Any

from ome_zarr_converters_tools.models._acquisition import OmeZarrOptions
from ome_zarr_converters_tools.models._tile_region import TiledImage


def write_tiled_image_as_zarr(
    tiled_image: TiledImage,
    resource: Any,
    ome_zarr_options: OmeZarrOptions,
) -> dict[str, Any]:
    """Write a TiledImage as a Zarr file.

    Args:
        tiled_image: TiledImage model to write.
        resource: Resource to write the Zarr file to.
        ome_zarr_options: OmeZarrOptions model to use for writing.
    """
    raise NotImplementedError("Writing TiledImage as Zarr is not implemented yet.")
