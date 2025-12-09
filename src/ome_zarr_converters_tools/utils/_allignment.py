from ome_zarr_converters_tools.models._acquisition import AlignmentCorrections
from ome_zarr_converters_tools.models._tile_region import TiledImage, TileRegion


def _align_xy_regions(regions: list[TileRegion]) -> list[TileRegion]:
    raise NotImplementedError("XY alignment is not implemented yet.")


def _align_z_regions(regions: list[TileRegion]) -> list[TileRegion]:
    raise NotImplementedError("Z alignment is not implemented yet.")


def _align_t_regions(regions: list[TileRegion]) -> list[TileRegion]:
    raise NotImplementedError("T alignment is not implemented yet.")


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


def align_regions(
    tiled_image: TiledImage, alignement_corrections: AlignmentCorrections
) -> TiledImage:
    """Align all the regions in a TiledImage to be consistent.

    This function modifies the TiledImages in place.

    Args:
        tiled_image: TiledImage model to align.
        alignement_corrections: AlignmentCorrections model to use for alignment.

    """
    fov_regions = tiled_image.group_by_fov()
    alligned_regions = []
    for regions in fov_regions.values():
        aligned = _align_regions(regions, alignement_corrections)
        alligned_regions.extend(aligned)
    tiled_image.regions = alligned_regions
    return tiled_image
