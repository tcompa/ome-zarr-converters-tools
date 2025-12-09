from typing import Any, Literal

from ome_zarr_converters_tools.models._tile_region import TiledImage, TileRegion
from ome_zarr_converters_tools.utils._roi_utils import move_roi_by


def _find_reference_regions(regions: list[TileRegion]) -> TileRegion:
    raise NotImplementedError("Finding reference regions is not implemented yet.")


def _find_tiling(
    regions: dict[str, TileRegion],
    tiling_mode: Literal["auto", "grid", "free", "inplace", "none"],
) -> dict[str, dict[str, float]]:
    raise NotImplementedError("Finding tiling is not implemented yet.")


# Proposal for tiling modes:
# - auto: Determine if grid or free based on regions.
# - grid: Tile regions into a regular grid pattern.
# - free: Tile regions using a snap to corners approach.
# - inplace: No tiling, keep original positions.
# - none: No tiling, write each FOV as separate image.

# Alternative: Implement each tiling mode as separate functions.
# - auto_tiling: ...
# - snap_to_grid: ...
# - snap_to_corners: ...
# - inplace_tiling or stage_position
# - no_tiling: ...


def _tile_regions(
    regions: list[TileRegion], vectror: dict[str, float]
) -> list[TileRegion]:
    for region in regions:
        region.roi = move_roi_by(region.roi, vectror)
    return regions


def tile_regions(
    tiled_image: TiledImage,
    tiling_mode: Literal["auto", "grid", "free", "inplace", "none"] = "auto",
) -> TiledImage:
    """Tile all the TiledImages to the reference region of the first TiledImage.

    This function modifies the TiledImages in place.

    Args:
        tiled_image: TiledImage model to tile.
        tiling_mode: Tiling mode to use.

    """
    fov_regions = tiled_image.group_by_fov()

    reference_regions = {}
    for key, regions in fov_regions.items():
        ref_region = _find_reference_regions(regions)
        reference_regions[key] = ref_region

    tiling_instructions = _find_tiling(reference_regions, tiling_mode)
    alligned_regions = []
    for key, regions in fov_regions.items():
        instruction = tiling_instructions[key]
        tiled = _tile_regions(regions, instruction)
        alligned_regions.extend(tiled)
    tiled_image.regions = alligned_regions
    return tiled_image
