import math
from typing import Any

import zarr
from ngio import PixelSize, RoiSlice, create_empty_ome_zarr
from ngio.tables import RoiTable
from ngio.utils._zarr_utils import NgioSupportedStore

from ome_zarr_converters_tools.models._acquisition import OmeZarrOptions, canonical_axes
from ome_zarr_converters_tools.models._tile_region import TiledImage, TileRegion
from ome_zarr_converters_tools.utils._roi_utils import bulk_roi_union


def _compute_fov_properties(
    regions: list[TileRegion],
) -> dict[str, Any]:
    raise NotImplementedError("This function is not yet implemented.")


def _compute_image_properties(
    regions: list[TileRegion],
    ome_zarr_options: OmeZarrOptions,
) -> dict[str, Any]:
    roi_union = bulk_roi_union([region.roi for region in regions])
    axes_shape = {}
    for roi_slice in roi_union.slices:
        length = roi_slice.length
        assert length is not None
        axes_shape[roi_slice.axis_name] = math.ceil(length)
    shape, axes, chunks = [], [], []
    for c_ax in canonical_axes:
        if c_ax in axes_shape:
            shape.append(axes_shape[c_ax])
            axes.append(c_ax)
            if c_ax == "x" or c_ax == "y":
                _chunks_size = min(axes_shape[c_ax], ome_zarr_options.max_xy_chunk)
                chunks.append(_chunks_size)
            elif c_ax == "z":
                chunks.append(ome_zarr_options.z_chunk)
            elif c_ax == "c":
                chunks.append(ome_zarr_options.c_chunk)
            elif c_ax == "t":
                chunks.append(ome_zarr_options.t_chunk)
            else:
                chunks.append(1)
    return {
        "shape": tuple(shape),
        "axes_names": axes,
        "chunks": tuple(chunks),
    }


def _region_to_pixel_coordinates(
    regions: list[TileRegion],
    pixel_size: PixelSize,
) -> list[TileRegion]:
    """Convert TileRegion ROIs from pixel coordinates to world coordinates.

    This function modifies the TileRegions in place.

    Args:
        regions: List of TileRegion models to convert.
        pixel_size: PixelSize model to use for conversion.
    """
    for region in regions:
        roi = region.roi.to_pixel(pixel_size=pixel_size)
        rounded_slices = []
        for ax_slice in roi.slices:
            start = ax_slice.start
            length = ax_slice.length
            assert start is not None and length is not None
            rounded_slice = RoiSlice(
                axis_name=ax_slice.axis_name,
                start=round(start),
                length=round(length),
            )
            rounded_slices.append(rounded_slice)
        region.roi = roi.model_copy(update={"slices": rounded_slices})
    return regions


def write_tiled_image_as_zarr(
    base_store: NgioSupportedStore,
    tiled_image: TiledImage,
    resource: Any,
    ome_zarr_options: OmeZarrOptions,
    overwrite: bool = True,
) -> dict[str, Any]:
    """Write a TiledImage as a Zarr file.

    Args:
        base_store: Base store to write the Zarr file to.
        tiled_image: TiledImage model to write.
        resource: Resource to write the Zarr file to.
        ome_zarr_options: OmeZarrOptions model to use for writing.
        overwrite: Whether to overwrite existing Zarr files.
    """
    tiled_image.regions = _region_to_pixel_coordinates(
        tiled_image.regions,
        tiled_image.pixel_size,
    )
    image_properties = _compute_image_properties(tiled_image.regions, ome_zarr_options)
    mode = "w" if overwrite else "w-"
    base_group = zarr.open_group(store=base_store, mode=mode, path=tiled_image.path)
    ome_zarr = create_empty_ome_zarr(
        store=base_group,
        pixelsize=tiled_image.pixelsize,
        z_spacing=tiled_image.z_spacing,
        time_spacing=tiled_image.t_spacing,
        levels=ome_zarr_options.num_levels,
        overwrite=overwrite,
        **image_properties,
    )
    image = ome_zarr.get_image()
    for region in tiled_image.regions:
        region_data = region.load_data(resource)
        region_data = region_data[None, None, None, ...]
        image.set_roi(roi=region.roi, patch=region_data)

    rois = []
    for key, regions in tiled_image.group_by_fov().items():
        roi_union = bulk_roi_union([region.roi for region in regions])
        roi_union.name = key
        rois.append(roi_union.to_world(pixel_size=tiled_image.pixel_size))
    roi_table = RoiTable(rois=rois)
    ome_zarr.add_table("FOV_ROI_table", roi_table, backend="csv")

    well_roi = ome_zarr.build_image_roi_table()
    ome_zarr.add_table("well_ROI_table", well_roi, backend="csv")
    return {}
