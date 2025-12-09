"""Functions to build TiledImage models from Tile models."""

from pathlib import Path
from typing import Any

import pandas as pd
import toml

from ome_zarr_converters_tools.models._acquisition import (
    AcquisitionDetails,
    ConverterOptions,
    FullContextBaseModel,
    HCSFromTableContext,
)
from ome_zarr_converters_tools.models._collection import ImageInPlate
from ome_zarr_converters_tools.models._loader import DefaultImageLoader
from ome_zarr_converters_tools.models._tile import BaseTile
from ome_zarr_converters_tools.models._tile_region import TiledImage
from ome_zarr_converters_tools.tools.tile_to_tiled_images import tiled_image_from_tiles


def build_default_image_loader(
    data: dict[str, Any],
) -> dict[str, Any]:
    """Build an image loader for a tile row dictionary."""
    image_loader_data = {}
    out_data = {}
    for key, value in data.items():
        if key in DefaultImageLoader.model_fields.keys():
            image_loader_data[key] = value
        else:
            out_data[key] = value
    image_loader = DefaultImageLoader(**image_loader_data)
    out_data["image_loader"] = image_loader
    return out_data


def build_plate_collection(
    data: dict[str, Any], plate_name: str, acquisition: int
) -> dict[str, Any]:
    """Build an ImageInPlate collection for a tile row dictionary."""
    collection_data = {}
    out_data = {}
    for key, value in data.items():
        if key in ImageInPlate.model_fields.keys():
            collection_data[key] = value
        else:
            out_data[key] = value
    collection = ImageInPlate(
        **collection_data, plate_path=plate_name, acquisition=acquisition
    )
    out_data["collection"] = collection
    return out_data


def _open_hcs_dir(
    acquisition_path: Path,
    table_name: str = "tiles.csv",
    acquisition_details_name: str = "acquisition_details.toml",
) -> tuple[pd.DataFrame, AcquisitionDetails]:
    """Open the HCS directory and read the tiles table.

    Args:
        acquisition_path: Path to the acquisition directory.
        table_name: Name of the table file.
        acquisition_details_name: Name of the acquisition details file.

    Returns:
        A tuple of the tiles DataFrame and AcquisitionDetails model.

    """
    table_path = acquisition_path / table_name
    df = pd.read_csv(table_path)

    with open(acquisition_path / acquisition_details_name) as f:
        acquisition_details_dict = toml.load(f)
        acquisition_details = AcquisitionDetails.model_validate(
            acquisition_details_dict
        )

    return df, acquisition_details


def _table_to_tiles(
    tiles_table: pd.DataFrame,
    context: FullContextBaseModel,
    plate_name: str,
    acquisition: int,
) -> list[BaseTile]:
    """Build tiles from a tiles table DataFrame.

    Args:
        tiles_table: DataFrame containing the tiles table.
        context: Full context model for the conversion.
        plate_name: Name of the plate.
        acquisition: Acquisition index.
    """
    tiles = []
    for _, row in tiles_table.iterrows():
        row_dict = row.to_dict()
        row_dict = build_default_image_loader(row_dict)
        row_dict = build_plate_collection(
            row_dict, plate_name=plate_name, acquisition=acquisition
        )

        tile = BaseTile[ImageInPlate, DefaultImageLoader].model_validate(
            row_dict,
            context=context,
        )
        tiles.append(tile)

    return tiles


def table_to_tiled_images(
    acquisition_path: Path,
    plate_name: str,
    acquisition: int,
    converter_options: ConverterOptions,
    table_name: str = "tiles.csv",
    acquisition_details_name: str = "acquisition_details.toml",
) -> list[TiledImage]:
    """Build tiles for HCS data from a table.

    Args:
        acquisition_path: Path to the acquisition directory.
        plate_name: Name of the plate.
        acquisition: Acquisition index.
        converter_options: Converter options.
        table_name: Name of the table file.
        acquisition_details_name: Name of the acquisition details file.
    """
    df, acquisition_details = _open_hcs_dir(
        acquisition_path=acquisition_path,
        table_name=table_name,
        acquisition_details_name=acquisition_details_name,
    )

    context = HCSFromTableContext(
        acquisition_path=acquisition_path,
        plate_name=plate_name,
        acquisition=acquisition,
        acquisition_details=acquisition_details,
        converter_options=converter_options,
    )

    tiles = _table_to_tiles(
        tiles_table=df,
        context=context,
        plate_name=plate_name,
        acquisition=acquisition,
    )
    tiled_images = tiled_image_from_tiles(
        tiles, context=context, resource=acquisition_path
    )
    return tiled_images
