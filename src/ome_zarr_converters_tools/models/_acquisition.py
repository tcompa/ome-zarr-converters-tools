"""Models for defining regions to be converted into OME-Zarr format."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CANONICAL_AXES_TYPE = Literal["t", "c", "z", "y", "x"]
canonical_axes: list[CANONICAL_AXES_TYPE] = ["t", "c", "z", "y", "x"]
COO_TYPE = Literal["world", "pixel"]
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class CoordinateSystem(BaseModel):
    start_x: COO_TYPE = "world"
    start_y: COO_TYPE = "world"
    start_z: COO_TYPE = "world"
    start_t: COO_TYPE = "world"
    length_x: COO_TYPE = "pixel"
    length_y: COO_TYPE = "pixel"
    length_z: COO_TYPE = "pixel"
    length_t: COO_TYPE = "pixel"


class AcquisitionDetails(BaseModel):
    coo_system: CoordinateSystem = Field(default_factory=CoordinateSystem)
    pixelsize: float = 1.0  # in micrometers
    z_spacing: float = 1.0  # in micrometers
    t_spacing: float = 1.0  # in micrometers
    channel_names: list[str] | None = None
    wavelengths: list[float] | None = None
    axes: list[CANONICAL_AXES_TYPE] = Field(
        default_factory=lambda: canonical_axes.copy(), min_length=2, max_length=5
    )
    data_type: str | None = None
    model_config = ConfigDict(extra="forbid")


class StageCorrections(BaseModel):
    flip_x: bool = False
    flip_y: bool = False
    swap_xy: bool = False
    model_config = ConfigDict(extra="forbid")


class AlignmentCorrections(BaseModel):
    align_xy: bool = False
    align_z: bool = False
    align_t: bool = False
    model_config = ConfigDict(extra="forbid")


class ImageOptions(BaseModel):
    num_levels: int = Field(default=5, ge=1)
    max_xy_chunk: int = Field(default=4096, ge=1)
    z_chunk: int = Field(default=10, ge=1)
    c_chunk: int = Field(default=1, ge=1)
    t_chunk: int = Field(default=1, ge=1)
    model_config = ConfigDict(extra="forbid")


class ConverterOptions(BaseModel):
    tiling_mode: Literal["auto", "grid", "free", "inplace", "none"] = "auto"
    stage_correction: StageCorrections = Field(default_factory=StageCorrections)
    alignment_correction: AlignmentCorrections = Field(
        default_factory=AlignmentCorrections
    )
    image_options: ImageOptions = Field(default_factory=ImageOptions)
    model_config = ConfigDict(extra="forbid")

    def split_tiles(self) -> bool:
        return self.tiling_mode == "none"


class FullContextConverterOptions(BaseModel):
    acquisition_details: AcquisitionDetails = Field(default_factory=AcquisitionDetails)
    converter_options: ConverterOptions = Field(default_factory=ConverterOptions)
    model_config = ConfigDict(extra="forbid")
