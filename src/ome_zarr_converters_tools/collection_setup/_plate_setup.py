"""Collection setup functions for OME-Zarr converters tools."""

from warnings import warn

import zarr
from ngio import DefaultNgffVersion, NgffVersions
from ngio.hcs import create_empty_plate
from ngio.hcs._plate import ImageInWellPath
from zarr.abc.store import Store

from ome_zarr_converters_tools.models._collection import (
    ImageInPlate,
)
from ome_zarr_converters_tools.models._tile_region import TiledImage


def sanitize_plate_name(plate_name: str) -> str:
    """Sanitize the plate name to be used as a Zarr group path."""
    if " " in plate_name or "/" in plate_name:
        warn(
            f"Plate name '{plate_name}' contains spaces or slashes, "
            "which will be replaced with underscores.",
            UserWarning,
            stacklevel=2,
        )
        plate_name = plate_name.replace(" ", "_").replace("/", "_")
    # Make sure it ends with .zarr
    if not plate_name.endswith(".zarr"):
        plate_name = f"{plate_name}.zarr"
    return plate_name


def setup_plates(
    store: Store,
    tiled_images: list[TiledImage],
    ngff_version: NgffVersions = DefaultNgffVersion,
) -> None:
    """Set up an ImageInPlate collection in the Zarr group."""
    assert isinstance(tiled_images[0].collection, ImageInPlate)
    plates = {}
    for tile in tiled_images:
        plate_name = tile.collection.plate_name
        if plate_name not in plates:
            plates[plate_name] = []
        image_in_well = ImageInWellPath(
            row=tile.collection.well_row,
            column=tile.collection.well_column,
            path=tile.collection.path_in_well(),
            acquisition_id=tile.collection.acquisition,
            acquisition_name=tile.collection.acquisition_name,
        )
        plates[plate_name].append(image_in_well)

    for plate_name, images in plates.items():
        plate_path = sanitize_plate_name(plate_name)
        group = zarr.create_group(store, overwrite=True, path=plate_path)
        create_empty_plate(
            store=group,
            name=plate_name,
            images=images,
            ngff_version=ngff_version,
        )
