"""Models for defining regions to be converted into OME-Zarr format."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ome_zarr_converters_tools.models._acquisition import (
    AcquisitionDetails,
    CoordinateSystem,
    FullContextConverterOptions,
)
from ome_zarr_converters_tools.models._collection import (
    CollectionInterface,
    build_collection,
)
from ome_zarr_converters_tools.models._loader import (
    ImageLoaderInterface,
    build_default_image_loader,
)
from ome_zarr_converters_tools.models._roi_v2 import (
    RoiSlice,
    RoiV2,
    pixel_to_world,
    world_to_pixel,
)

CANONICAL_AXES_TYPE = Literal["t", "c", "z", "y", "x"]
canonical_axes: list[CANONICAL_AXES_TYPE] = ["t", "c", "z", "y", "x"]
COO_TYPE = Literal["world", "pixel"]
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def safe_to_world(
    start: float,
    spacing: float,
    coo_system: COO_TYPE,
    eps: float = 1e-6,
) -> float:
    """Convert from world to pixel and back to world to ensure alignment."""
    if coo_system == "world":
        pixel_coord = world_to_pixel(start, spacing)
        world_coord = pixel_to_world(pixel_coord, spacing)
        if abs(world_coord - start) > eps:
            raise ValueError(
                f"Coordinate {start}, with spacing {spacing}, "
                f"cannot be accurately represented in pixel coordinates."
            )
        return world_coord
    world_coord = pixel_to_world(start, spacing)
    pixel_coord = world_to_pixel(world_coord, spacing)
    if abs(pixel_coord - start) > eps:
        raise ValueError(
            f"Coordinate {start}, with spacing {spacing}, "
            f"cannot be accurately represented in world coordinates."
        )
    return world_coord


class Tile(BaseModel):
    fov_name: str
    # Positions
    start_x: float
    start_y: float
    start_z: float = 0.0
    start_c: int = 0
    start_t: float = 0.0
    # Sizes
    length_x: float = Field(gt=0)
    length_y: float = Field(gt=0)
    length_z: float = Field(default=1.0, gt=0)
    length_c: int = Field(default=1, gt=0)
    length_t: float = Field(default=1.0, gt=0)
    # Collection model defining how to build the path to the image(s)
    collection: CollectionInterface
    # Image loader
    image_loader: ImageLoaderInterface

    # Additional acquisition details
    # This if not provided, will be filled from context
    pixelsize: float = 1.0  # in micrometers
    z_spacing: float = 1.0  # in micrometers
    t_spacing: float = 1.0  # in micrometers
    channel_names: list[str] | None = None
    wavelengths: list[float] | None = None
    axes: list[CANONICAL_AXES_TYPE]
    coo_system: CoordinateSystem
    # Full context
    full_context: FullContextConverterOptions
    model_config = ConfigDict(extra="allow")

    @field_validator("channel_names", "wavelengths", mode="before")
    def split_channel_names(cls, v: Any) -> Any:
        if isinstance(v, str):
            return [name.strip() for name in v.split("/")]
        return v

    @model_validator(mode="before")
    def fill_from_context(cls, data: dict[str, Any], info: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if info.context is None:
            return data

        acq_details: AcquisitionDetails = info.context.acquisition_details
        acq_fields = AcquisitionDetails.model_fields.keys()
        self_fields = Tile.model_fields.keys()
        for field in acq_fields:
            if field in self_fields and field not in data:
                data[field] = getattr(acq_details, field)

        if "full_context" not in data:
            data["full_context"] = info.context
        return data

    def to_roi(self) -> RoiV2:
        """Convert the Tile to a RoiV2."""
        spacing = {
            "x": self.pixelsize,
            "y": self.pixelsize,
            "z": self.z_spacing,
            "t": self.t_spacing,
        }
        stage_correction = self.full_context.converter_options.stage_correction
        roi_slices = {}
        for ax in self.axes:
            start_field = f"start_{ax}"
            start = getattr(self, start_field)
            start_coo_system = getattr(self.coo_system, start_field, None)
            if start_coo_system is not None:
                start = safe_to_world(start, spacing[ax], start_coo_system)

            if ax == "x" and stage_correction.flip_x:
                start = -start
            if ax == "y" and stage_correction.flip_y:
                start = -start

            length_field = f"length_{ax}"
            length = getattr(self, length_field)
            length_coo_system = getattr(self.coo_system, length_field, None)
            if length_coo_system is not None:
                length = safe_to_world(length, spacing[ax], length_coo_system)
            roi_slices[ax] = RoiSlice(start=start, length=length, axis_name=ax)

        if stage_correction.swap_xy:
            y_slice = roi_slices["y"]
            y_slice.axis_name = "x"
            x_slice = roi_slices["x"]
            x_slice.axis_name = "y"
            roi_slices["x"] = y_slice
            roi_slices["y"] = x_slice

        origins = {}
        for ax, roi_slice in roi_slices.items():
            origins[f"{ax}_micrometer_original"] = roi_slice.start

        return RoiV2(
            name=self.fov_name,
            slices=list(roi_slices.values()),
            space="world",
            **origins,
        )


def build_tiles(
    data: dict[str, Any], full_context: FullContextConverterOptions
) -> Tile:
    data = build_collection(data)
    data = build_default_image_loader(data, context=full_context.acquisition_details)
    return Tile.model_validate(
        data,
        context=full_context,
    )
