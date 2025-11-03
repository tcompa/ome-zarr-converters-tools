"""Models for defining regions to be converted into OME-Zarr format."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import tifffile
from PIL import Image
from pydantic import BaseModel, ConfigDict, model_validator

if TYPE_CHECKING:
    from ome_zarr_converters_tools.models._acquisition import AcquisitionDetails


class ImageLoaderInterface(BaseModel, ABC):
    data_type: str | None = None

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="before")
    def fill_from_context(cls, data: dict[str, Any], info: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if info.context is None:
            return data

        acq_details: AcquisitionDetails = info.context
        if "data_type" not in data or data["data_type"] is None:
            data["data_type"] = acq_details.data_type
        return data

    @abstractmethod
    def load_data(self, resource: Any = None) -> np.ndarray:
        """Load the image data as a Dask array."""
        pass

    def safe_data_type(self, resource: Any = None) -> str:
        """Return the data type of the loaded image.

        If the data type is not set,
        it will be inferred from the loaded image.
        """
        if self.data_type is None:
            self.data_type = str(self.load_data(resource).dtype)
        return self.data_type


class DefaultImageLoader(ImageLoaderInterface):
    file_name: str
    base_dir: str | None = None

    def load_data(self, resource: Any = None) -> np.ndarray:
        """Load the image data as a NumPy array."""
        if self.base_dir is not None:
            path = Path(self.base_dir) / "data" / self.file_name
        else:
            path = Path(self.file_name)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if path.suffix.lower() in [".tiff", ".tif"]:
            with tifffile.TiffFile(path) as tif:
                image = tif.asarray()
        elif path.suffix.lower() in [".png", ".jpg", ".jpeg", ".bmp"]:
            image = np.array(Image.open(path))

        elif path.suffix.lower() == ".npy":
            image = np.load(path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        return image


def build_default_image_loader(
    data: dict[str, Any],
    data_type: str | None = None,
    base_dir: str | None = None,
    key_name: str = "image_loader",
) -> dict[str, Any]:
    """Create a DefaultImageLoader from a dictionary."""
    if "data_type" not in data:
        data["data_type"] = data_type
    if base_dir is not None:
        data["base_dir"] = base_dir
    data_loader = DefaultImageLoader(**data)
    data = {k: v for k, v in data.items() if k not in DefaultImageLoader.model_fields}
    data[key_name] = data_loader
    return data
