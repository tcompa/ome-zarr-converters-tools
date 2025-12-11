import warnings
from typing import Literal

from ome_zarr_converters_tools.models._acquisition import AlignmentCorrections
from ome_zarr_converters_tools.models._tile_region import TiledImage, TileRegion


def _align_xy_regions(regions: list[TileRegion]) -> list[TileRegion]:
    warnings.warn(
        "XY alignment is not implemented yet. Returning regions unchanged.",
        UserWarning,
        stacklevel=2,
    )
    return regions


def _align_z_regions(regions: list[TileRegion]) -> list[TileRegion]:
    warnings.warn(
        "Z alignment is not implemented yet. Returning regions unchanged.",
        UserWarning,
        stacklevel=2,
    )
    return regions


def _align_t_regions(regions: list[TileRegion]) -> list[TileRegion]:
    warnings.warn(
        "T alignment is not implemented yet. Returning regions unchanged.",
        UserWarning,
        stacklevel=2,
    )
    return regions


def _align_regions(
    regions: list[TileRegion], alignment_corrections: AlignmentCorrections
) -> list[TileRegion]:
    if alignment_corrections.align_xy:
        regions = _align_xy_regions(regions)
    if alignment_corrections.align_z:
        regions = _align_z_regions(regions)
    if alignment_corrections.align_t:
        regions = _align_t_regions(regions)
    return regions


def apply_fov_alignment_corrections(
    tiled_image: TiledImage, alignment_corrections: AlignmentCorrections
) -> TiledImage:
    """Align all the regions in a TiledImage to be consistent.

    The function:
        -groups regions by their field of view (FOV)
        -applies alignment corrections to each group
        -updates the TiledImage with the aligned regions

    Args:
        tiled_image: TiledImage model to align.
        alignment_corrections: AlignmentCorrections model specifying which
            corrections to apply.

    """
    fov_regions = tiled_image.group_by_fov()
    alligned_regions = []
    for regions in fov_regions.values():
        aligned = _align_regions(regions, alignment_corrections)
        alligned_regions.extend(aligned)
    tiled_image.regions = alligned_regions
    return tiled_image


def apply_align_to_pixel_grid(
    tiled_image: TiledImage, mode: Literal["round", "floor", "ceil"] = "floor"
) -> TiledImage:
    """Align the start position to the pixel grid.

    For each tile, adjust the start position to the nearest pixel grid position.
    """
    warnings.warn(
        "Aligning to pixel grid is not implemented yet. "
        "Returning TiledImage unchanged.",
        UserWarning,
        stacklevel=2,
    )
    return tiled_image


def apply_remove_offsets(tiled_image: TiledImage) -> TiledImage:
    """Remove any offsets from the tile positions.

    This will find the minimum position in each dimension and
        subtract it from all tiles.
    """
    warnings.warn(
        "Removing offsets is not implemented yet. Returning TiledImage unchanged.",
        UserWarning,
        stacklevel=2,
    )
    return tiled_image
