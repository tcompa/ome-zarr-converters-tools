"""Models for defining regions to be converted into OME-Zarr format."""

from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    DirectoryPath,
    Field,
    field_validator,
)

CANONICAL_AXES_TYPE = Literal["t", "c", "z", "y", "x"]
canonical_axes: list[CANONICAL_AXES_TYPE] = ["t", "c", "z", "y", "x"]
COO_TYPE = Literal["world", "pixel"]
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
TILING_MODES = Literal[
    "auto", "snap_to_grid", "snap_to_corners", "inplace", "no_tiling"
]


class AcquisitionDetails(BaseModel):
    """Details about the acquisition.

    These can be either provided by the user or inferred from the data.
    """

    # Determine the coordinate system for start and length values
    start_x_coo: COO_TYPE = "world"
    start_y_coo: COO_TYPE = "world"
    start_z_coo: COO_TYPE = "world"
    start_t_coo: COO_TYPE = "world"
    length_x_coo: COO_TYPE = "pixel"
    length_y_coo: COO_TYPE = "pixel"
    length_z_coo: COO_TYPE = "pixel"
    length_t_coo: COO_TYPE = "pixel"
    # Spacing information
    pixelsize: float = Field(default=1.0, gt=0.0)  # in micrometers
    z_spacing: float = Field(default=1.0, gt=0.0)  # in micrometers
    t_spacing: float = Field(default=1.0, gt=0.0)  # in micrometers

    # Channel information
    channel_names: list[str] | None = None
    wavelengths: list[float] | None = None

    # Axes order to be used for the data (should be a subset of canonical axes)
    axes: list[CANONICAL_AXES_TYPE] = Field(
        default_factory=lambda: canonical_axes.copy(), min_length=2, max_length=5
    )

    # Data type of the image data (if known)
    data_type: str | None = None

    model_config = ConfigDict(extra="forbid")

    @classmethod
    @field_validator("axes")
    def validate_axes(cls, v: list[CANONICAL_AXES_TYPE]) -> list[CANONICAL_AXES_TYPE]:
        """Validate that axes are in canonical order."""
        for i in range(1, len(v)):
            if canonical_axes.index(v[i]) <= canonical_axes.index(v[i - 1]):
                raise ValueError("Axes must be in canonical order: t, c, z, y, x")
        return v


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


class OmeZarrOptions(BaseModel):
    num_levels: int = Field(default=5, ge=1)
    max_xy_chunk: int = Field(default=4096, ge=1)
    z_chunk: int = Field(default=10, ge=1)
    c_chunk: int = Field(default=1, ge=1)
    t_chunk: int = Field(default=1, ge=1)
    model_config = ConfigDict(extra="forbid")


class ConverterOptions(BaseModel):
    tiling_mode: TILING_MODES = "auto"
    stage_correction: StageCorrections = Field(default_factory=StageCorrections)
    alignment_correction: AlignmentCorrections = Field(
        default_factory=AlignmentCorrections
    )
    omezarr_options: OmeZarrOptions = Field(default_factory=OmeZarrOptions)
    model_config = ConfigDict(extra="forbid")


class FullContextBaseModel(BaseModel):
    """Base model for context information during conversion."""

    acquisition_details: AcquisitionDetails
    converter_options: ConverterOptions
    model_config = ConfigDict(extra="forbid")


class HCSFromTableContext(FullContextBaseModel):
    """Context model for HCS data from a table."""

    acquisition_path: DirectoryPath
    plate_name: str = "plate"
    acquisition: int = Field(default=0, ge=0)
    model_config = ConfigDict(extra="forbid")
