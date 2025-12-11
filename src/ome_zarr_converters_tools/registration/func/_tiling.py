import warnings

import numpy as np
from ngio import Roi, RoiSlice

from ome_zarr_converters_tools.models._acquisition import TILING_MODES
from ome_zarr_converters_tools.models._roi_utils import move_roi_by, roi_to_roi_distance
from ome_zarr_converters_tools.models._tile_region import TiledImage, TileSlice


def _find_reference_regions(regions: list[TileSlice]) -> TileSlice:
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
    regions: dict[str, TileSlice],
    tiling_mode: TILING_MODES,
) -> dict[str, dict[str, float]]:
    if tiling_mode in ["inplace", "no_tiling"]:
        # No tiling needed Keep all regions in place
        return {key: {"x": 0.0, "y": 0.0, "z": 0.0, "t": 0.0} for key in regions.keys()}
    if tiling_mode == "auto":
        warnings.warn(
            "Auto tiling mode is not implemented yet. Defaulting to 'inplace'.",
            UserWarning,
            stacklevel=2,
        )
        return {key: {"x": 0.0, "y": 0.0, "z": 0.0, "t": 0.0} for key in regions.keys()}

    if tiling_mode == "snap_to_corners":
        warnings.warn(
            "Snap to corners tiling mode is not implemented yet. "
            "Defaulting to 'inplace'.",
            UserWarning,
            stacklevel=2,
        )
        return {key: {"x": 0.0, "y": 0.0, "z": 0.0, "t": 0.0} for key in regions.keys()}

    if tiling_mode == "snap_to_grid":
        warnings.warn(
            "Snap to grid tiling mode is not implemented yet. Defaulting to 'inplace'.",
            UserWarning,
            stacklevel=2,
        )
        return {key: {"x": 0.0, "y": 0.0, "z": 0.0, "t": 0.0} for key in regions.keys()}

    raise ValueError(f"Tiling mode '{tiling_mode}' is not recognized.")


def _tile_regions(
    regions: list[TileSlice], vectror: dict[str, float]
) -> list[TileSlice]:
    for region in regions:
        region.roi = move_roi_by(region.roi, vectror)
    return regions


def apply_mosaic_tiling(
    tiled_image: TiledImage,
    tiling_mode: TILING_MODES,
) -> TiledImage:
    """Tile all the TiledImages to the reference region of the first TiledImage.

    This function modifies the TiledImages in place.

    Args:
        tiled_image: TiledImage model to tile.
        tiling_mode: Tiling mode to use.

    """
    fov_tiles = tiled_image.group_by_fov()

    reference_regions = {}
    for fov_tile in fov_tiles:
        ref_region = _find_reference_regions(fov_tile.regions)
        reference_regions[fov_tile.fov_name] = ref_region

    tiling_instructions = _find_tiling(reference_regions, tiling_mode)
    alligned_regions = []
    for fov_tile in fov_tiles:
        instruction = tiling_instructions[fov_tile.fov_name]
        tiled = _tile_regions(fov_tile.regions, instruction)
        alligned_regions.extend(tiled)
    tiled_image.regions = alligned_regions
    return tiled_image
