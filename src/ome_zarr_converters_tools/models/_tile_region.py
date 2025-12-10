"""Models for defining regions to be converted into OME-Zarr format."""

from typing import Any, Generic, Literal, Self

import numpy as np
from ngio import PixelSize, Roi
from pydantic import BaseModel, ConfigDict, Field

from ome_zarr_converters_tools.models._collection import CollectionInterfaceType
from ome_zarr_converters_tools.models._loader import (
    ImageLoaderInterfaceType,
)
from ome_zarr_converters_tools.models._tile import BaseTile

CANONICAL_AXES_TYPE = Literal["t", "c", "z", "y", "x"]
COO_TYPE = Literal["world", "pixel"]


class TileRegion(BaseModel, Generic[ImageLoaderInterfaceType]):
    # Region
    roi: Roi
    image_loader: ImageLoaderInterfaceType
    model_config = ConfigDict(extra="forbid")

    @classmethod
    def from_tile(cls, tile: BaseTile) -> Self:
        """Create a TileRegion from a Tile."""
        return cls(
            roi=tile.to_roi(),
            # collection=tile.collection,
            image_loader=tile.image_loader,
        )

    def load_data(self, resource: Any) -> np.ndarray:
        """Load the image data for this TileRegion using the image loader."""
        return self.image_loader.load_data(resource=resource)


class TiledImage(BaseModel, Generic[CollectionInterfaceType, ImageLoaderInterfaceType]):
    regions: list[TileRegion[ImageLoaderInterfaceType]] = Field(default_factory=list)
    path: str
    name: str | None = None
    pixelsize: float = 1.0
    z_spacing: float = 1.0
    t_spacing: float = 1.0
    data_type: str
    channel_names: list[str] | None = None
    wavelengths: list[float] | None = None
    axes: list[CANONICAL_AXES_TYPE]
    collection: CollectionInterfaceType

    model_config = ConfigDict(extra="forbid")

    def group_by_fov(self) -> dict[str, list[TileRegion]]:
        """Group TileRegions by field of view name."""
        fov_dict: dict[str, list[TileRegion]] = {}
        for region in self.regions:
            fov_name = region.roi.name
            if fov_name is None:
                raise ValueError("TileRegion ROI must have a name to group by FOV.")
            if fov_name not in fov_dict:
                fov_dict[fov_name] = []
            fov_dict[fov_name].append(region)
        return fov_dict

    @property
    def pixel_size(self) -> PixelSize:
        """Return the PixelSize of the TiledImage."""
        return PixelSize(
            x=self.pixelsize,
            y=self.pixelsize,
            z=self.z_spacing,
            t=self.t_spacing,
        )

    def add_tile(self, tile: BaseTile) -> None:
        """Add a Tile to the TiledImage as a TileRegion."""
        if self.channel_names != tile.channel_names:
            raise ValueError(
                "Tile channel names do not match TiledImage channel names."
            )
        if self.wavelengths != tile.wavelengths:
            raise ValueError("Tile wavelengths do not match TiledImage wavelengths.")
        if self.axes != tile.axes:
            raise ValueError("Tile axes do not match TiledImage axes.")
        if self.pixelsize != tile.pixelsize:
            raise ValueError("Tile pixelsize does not match TiledImage pixelsize.")
        if self.z_spacing != tile.z_spacing:
            raise ValueError("Tile z_spacing does not match TiledImage z_spacing.")
        if self.t_spacing != tile.t_spacing:
            raise ValueError("Tile t_spacing does not match TiledImage t_spacing.")
        tile_region = TileRegion.from_tile(tile)
        self.regions.append(tile_region)
