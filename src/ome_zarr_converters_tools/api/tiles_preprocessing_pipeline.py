"""Functions to build TiledImage models from Tile models."""

from ome_zarr_converters_tools.collection_setup import (
    SetupCollectionStep,
    setup_collection,
)
from ome_zarr_converters_tools.filters import FilterStep, apply_filter_pipeline
from ome_zarr_converters_tools.models import (
    BaseTile,
    ContextModel,
    TiledImage,
)
from ome_zarr_converters_tools.utils import tiled_image_from_tiles
from ome_zarr_converters_tools.validators import ValidatorStep, apply_validator_pipeline


def tiles_preprocessing_pipeline(
    tiles: list[BaseTile],
    context: ContextModel,
    filters: list[FilterStep] | None = None,
    validators: list[ValidatorStep] | None = None,
    setup_collection_step: SetupCollectionStep | None = None,
) -> list[TiledImage]:
    """Process tiles through the preprocessing pipeline to create TiledImages.

    This function applies optional filters to the input tiles and then
    constructs TiledImage models from the processed tiles.

    Args:
        tiles: List of Tile models to process.
        context: Full context model for the conversion.
        filters: Optional list of filter steps to apply to the tiles.
        validators: Optional list of validator steps to apply to the tiles.
        setup_collection_step: Optional configuration for the collection setup step.

    Returns:
        A list of TiledImage models created from the processed tiles.
    """
    if filters is not None:
        tiles = apply_filter_pipeline(tiles, filters_config=filters)
    tiled_images = tiled_image_from_tiles(
        tiles=tiles,
        context=context,
    )
    if validators is not None:
        tiled_images = apply_validator_pipeline(
            tiled_images, validators_config=validators
        )
    if setup_collection_step is not None:
        setup_collection(
            tiled_images=tiled_images,
            setup_collection_step=setup_collection_step,
        )
    return tiled_images
