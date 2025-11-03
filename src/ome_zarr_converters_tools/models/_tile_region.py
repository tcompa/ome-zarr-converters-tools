"""Models for defining regions to be converted into OME-Zarr format."""

from typing import Literal, Self

from ngio import PixelSize
from pydantic import BaseModel, ConfigDict, Field

from ome_zarr_converters_tools.models._collection import (
    CollectionInterface,
)
from ome_zarr_converters_tools.models._loader import (
    ImageLoaderInterface,
)
from ome_zarr_converters_tools.models._roi_v2 import RoiV2
from ome_zarr_converters_tools.models._tile import Tile

CANONICAL_AXES_TYPE = Literal["t", "c", "z", "y", "x"]
canonical_axes: list[CANONICAL_AXES_TYPE] = ["t", "c", "z", "y", "x"]
COO_TYPE = Literal["world", "pixel"]
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class TileRegion(BaseModel):
    # Region
    roi: RoiV2
    # Collection model defining how to build the path to the image(s)
    collection: CollectionInterface
    # Image loader
    image_loader: ImageLoaderInterface
    model_config = ConfigDict(extra="forbid")

    @classmethod
    def from_tile(cls, tile: Tile) -> Self:
        """Create a TileRegion from a Tile."""
        return cls(
            roi=tile.to_roi(),
            collection=tile.collection,
            image_loader=tile.image_loader,
        )


class TiledImage(BaseModel):
    regions: list[TileRegion] = Field(default_factory=list)
    pixelsize: float = 1.0
    z_spacing: float = 1.0
    t_spacing: float = 1.0
    channel_names: list[str] | None = None
    wavelengths: list[float] | None = None
    axes: list[CANONICAL_AXES_TYPE]

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

    def pixel_size(self) -> PixelSize:
        """Return the PixelSize of the TiledImage."""
        return PixelSize(
            x=self.pixelsize,
            y=self.pixelsize,
            z=self.z_spacing,
            t=self.t_spacing,
        )

    def add_tile(self, tile: Tile) -> None:
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


def build_tiled_images(
    tiles: list[Tile], split_tiles: bool = False
) -> list[TiledImage]:
    """Create a TiledImage from a dictionary.

    Args:
        tiles: List of Tile models to build the TiledImage from.
        split_tiles: If True, each field of view will be in its own TiledImage.
            otherwise, all tiles will be combined into a single TiledImage.

    Returns:
        A TiledImage model.

    """
    tiled_images = {}
    for tile in tiles:
        suffix = "" if not split_tiles else f"_{tile.fov_name}"
        path = tile.collection.path(suffix=suffix)
        if path not in tiled_images:
            tiled_images[path] = TiledImage(
                regions=[],
                channel_names=tile.channel_names,
                wavelengths=tile.wavelengths,
                pixelsize=tile.pixelsize,
                z_spacing=tile.z_spacing,
                t_spacing=tile.t_spacing,
                axes=tile.axes,
            )
        tiled_images[path].add_tile(tile)
    return list(tiled_images.values())
