import numpy as np
from ngio import Roi, RoiSlice

from ome_zarr_converters_tools.models._acquisition import TILING_MODES
from ome_zarr_converters_tools.models._tile_region import TiledImage, TileRegion
from ome_zarr_converters_tools.utils._roi_utils import move_roi_by, roi_to_roi_distance


def _find_reference_regions(regions: list[TileRegion]) -> TileRegion:
    min_dist = np.inf
    reference_region = regions[0]
    reference_region_roi = regions[0].roi
    zero_slices = []
    for roi_slice in reference_region_roi.slices:
        zero_slices.append(
            RoiSlice(axis_name=roi_slice.axis_name, start=0, length=None)
        )
    roi_zero = Roi(name=None, slices=zero_slices)
    for region in regions:
        dist = roi_to_roi_distance(region.roi, roi_zero)
        if dist < min_dist:
            min_dist = dist
            reference_region = region
    return reference_region


def _find_tiling(
    regions: dict[str, TileRegion],
    tiling_mode: TILING_MODES,
) -> dict[str, dict[str, float]]:
    if tiling_mode in ["inplace", "no_tiling"]:
        # No tiling needed Keep all regions in place
        return {key: {"x": 0.0, "y": 0.0, "z": 0.0, "t": 0.0} for key in regions.keys()}
    raise NotImplementedError(
        "Tiling modes other than inplace and no_tiling are not implemented yet."
    )


def _tile_regions(
    regions: list[TileRegion], vectror: dict[str, float]
) -> list[TileRegion]:
    for region in regions:
        region.roi = move_roi_by(region.roi, vectror)
    return regions


def tile_regions(
    tiled_image: TiledImage,
    tiling_mode: TILING_MODES,
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
