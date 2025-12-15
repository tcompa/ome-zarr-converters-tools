"""Utilities to validate a regular grid of tiles."""

from typing import NamedTuple

import numpy as np
from pydantic import BaseModel

from ome_zarr_converters_tools.models._tile_region import TileSlice


class BBox(NamedTuple):
    x: float
    y: float
    x_len: float
    y_len: float


class GripPoint(NamedTuple):
    x: float
    y: float


def tiles_to_boxes(tiles: list[TileSlice]) -> list[BBox]:
    """Convert a list of TileSlice to a list of Box."""
    boxes = []
    for tile in tiles:
        roi = tile.roi
        if roi.space == "world":
            raise ValueError("Tiling is only supported for tiles in pixel coordinates.")
        slice_x = tile.roi.get("x")
        assert slice_x is not None
        start_x = slice_x.start
        length_x = slice_x.length
        assert start_x is not None and length_x is not None

        slice_y = tile.roi.get("y")
        assert slice_y is not None
        start_y = slice_y.start
        length_y = slice_y.length
        assert start_y is not None and length_y is not None
        box = BBox(x=start_x, y=start_y, x_len=length_x, y_len=length_y)
        boxes.append(box)
    return boxes


def _find_grid_size(bboxes: list[BBox], offset_x, offset_y) -> tuple[int, int]:
    """Find the grid size of a list of tiles."""
    x = [bbox.x for bbox in bboxes]
    y = [bbox.y for bbox in bboxes]
    num_x = int(np.round(max(x) / offset_x)) + 1
    num_y = int(np.round(max(y) / offset_y)) + 1
    return num_x, num_y


def build_correct_grid_points(
    boxes: list[BBox], offset_x: float, offset_y: float
) -> list[GripPoint]:
    """Build a list of grid points from a list of boxes."""
    grid_points = []
    for box in boxes:
        grid_x = round(box.x / offset_x) * offset_x
        grid_y = round(box.y / offset_y) * offset_y
        grid_point = GripPoint(x=grid_x, y=grid_y)
        grid_points.append(grid_point)
    return grid_points


class GridSetup(BaseModel):
    """Grid setup for a list of tiles.

    Attributes:
        size_x (float): Size of each tile in the x direction.
        size_y (float): Size of each tile in the y direction.
        offset_x (float): Offset of each tile in the x direction.
        offset_y (float): Offset of each tile in the y direction.
        num_x (int): Number of tiles in the x direction.
        num_y (int): Number of tiles in the y direction.

    """

    length_x: float = 0.0
    length_y: float = 0.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    num_x: int = 0
    num_y: int = 0


def check_if_regular_grid(tiles: list[TileSlice]) -> GridSetup:
    """Find the grid size of a list of tiles."""
    if len(tiles) == 0:
        raise ValueError("Empty list of tiles")

    if len(tiles) == 1:
        raise ValueError("Only one tile")

    bboxes = tiles_to_boxes(tiles)
    # ------------------------------------------
    # Test 1: Check if all lengths are the same
    # ------------------------------------------
    tiles_length_x = [bbox.x_len for bbox in bboxes]
    if np.allclose(tiles_length_x, tiles_length_x[0]):
        length_x = tiles_length_x[0]
    else:
        all_lengths = np.unique(tiles_length_x)
        raise ValueError(f"Not all lengths are the same: {all_lengths}")

    tiles_length_y = [bbox.y_len for bbox in bboxes]
    if len(tiles_length_y) == 0:
        raise ValueError("Empty list of tiles")

    if np.allclose(tiles_length_y, tiles_length_y[0]):
        length_y = tiles_length_y[0]
    else:
        all_lengths = np.unique(tiles_length_y)
        raise ValueError(f"Not all lengths are the same: {all_lengths}")
    # ------------------------------------------
    # Test 2: Check if all offsets are the same
    # ------------------------------------------
    # Find the tiles offsets
    pos_top_l_x = [box.x for box in bboxes]
    pos_top_l_x = np.sort(pos_top_l_x)
    offsets_x = np.diff(pos_top_l_x)
    offsets_x = offsets_x[offsets_x > 1e-6].tolist()

    if len(offsets_x) == 0:
        offset_x = 1.0
    elif np.allclose(offsets_x, offsets_x[0]):
        offset_x = offsets_x[0]
    else:
        # Not all offsets are the same
        unique_offsets = np.unique(offsets_x)
        raise ValueError(f"Not all x offsets are the same: {unique_offsets}")

    pos_top_l_y = [box.y for box in bboxes]
    pos_top_l_y = np.sort(pos_top_l_y)
    offsets_y = np.diff(pos_top_l_y)
    offsets_y = offsets_y[offsets_y > 1e-6].tolist()

    if len(offsets_y) == 0:
        offset_y = 1.0
    elif np.allclose(offsets_y, offsets_y[0]):
        offset_y = offsets_y[0]
    else:
        # Not all offsets are the same
        unique_offsets = np.unique(offsets_y)
        raise ValueError(f"Not all y offsets are the same: {unique_offsets}")
    # ------------------------------------------
    # Test 3: Check the edge case where the grid is slanted
    # ------------------------------------------
    if len(bboxes) > 2:
        for bbox in bboxes[1:]:
            offset_x = bbox.x - bboxes[0].x
            offset_y = bbox.y - bboxes[0].y
            if offset_x < 1e-6 or offset_y < 1e-6:
                # All good the grid is not slanted
                break
        else:
            raise ValueError("The grid is slanted")
    # Return the grid setup
    num_x, num_y = _find_grid_size(bboxes, offset_x, offset_y)
    return GridSetup(
        length_x=length_x,
        length_y=length_y,
        offset_x=offset_x,
        offset_y=offset_y,
        num_x=num_x,
        num_y=num_y,
    )


def _apply_snap_to_grid(
    tiles: list[TileSlice], grid_setup: GridSetup
) -> list[TileSlice]:
    """Remove overlap from a list of tiles that follow a regular grid."""
    # z, c, t = tiles[0].top_l.z, tiles[0].top_l.c, tiles[0].top_l.t

    output_tiles = []
    # The grid tolerance is set to 1% of the grid length
    grid_tolerance = min(grid_setup.length_x, grid_setup.length_y) / 100
    for i in range(grid_setup.num_x):
        for j in range(grid_setup.num_y):
            # X-Y position in the input grid
            x_in = i * grid_setup.offset_x
            y_in = j * grid_setup.offset_y

            # X-Y position in the output grid
            x_out = i * grid_setup.length_x
            y_out = j * grid_setup.length_y

            # Find if a bounding box is close to the (x_in, y_in) position
            point = Point(x_in, y_in, z=z, c=c, t=t)
            distances = [(point - bbox.top_l).lengthXY() for bbox in tiles]
            min_dist = np.min(distances)
            closest_bbox = tiles[np.argmin(distances)]

            if min_dist < grid_tolerance:
                # Move the bounding box to the (x_out, y_out) position
                top_l = Point(x_out, y_out, z=z, c=c, t=t)
                new_tile = closest_bbox.derive_from_diag(top_l, diag=closest_bbox.diag)
                output_tiles.append(new_tile)

    if len(output_tiles) != len(tiles):
        raise ValueError("Something went wrong with the grid tiling resolution.")
    return output_tiles


def find_snap_to_grid_offset(
    tiles: dict[str, TileSlice],
) -> dict[str, dict[str, float]]:
    """Remove overlap from a list of tiles by snapping them to a regular grid."""
    grid_setup = check_if_regular_grid(list(tiles.values()))
    new_starts = {}
    for name, tile in tiles.items():
        slice_x = tile.roi.get("x")
        assert slice_x is not None
        x = slice_x.start
        assert x is not None
        slice_y = tile.roi.get("y")
        assert slice_y is not None
        y = slice_y.start
        assert y is not None
        x_grid = x / grid_setup.offset_x * grid_setup.length_x
        y_grid = y / grid_setup.offset_y * grid_setup.length_y
        new_starts[name] = {"x": x_grid - x, "y": y_grid - y}
    return new_starts
