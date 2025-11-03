"""Models for defining regions to be converted into OME-Zarr format."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class CollectionInterface(BaseModel, ABC):
    model_config = ConfigDict(extra="ignore")

    @abstractmethod
    def path(self, suffix: str = "") -> str:
        pass


class SingleImage(CollectionInterface):
    image_path: str

    def path(self, suffix: str = "") -> str:
        return f"{self.image_path}{suffix}"


class ImageInPlate(CollectionInterface):
    row: str
    column: int = Field(ge=1)
    acquisition: int = Field(default=0, ge=0)

    def path(self, suffix: str = "") -> str:
        return f"{self.row}{self.column}/{self.acquisition}{suffix}"

    @field_validator("row", mode="before")
    def row_to_str(cls, v: Any) -> Any:
        if isinstance(v, int):
            if v < 1 or v >= len(ALPHABET):
                raise ValueError(
                    f"Row index {v} out of range. "
                    f"Must be between 1 and {len(ALPHABET) - 1}"
                )
            return ALPHABET[v - 1]
        return v


def build_collection(
    data: dict[str, Any],
    key_name: str = "collection",
) -> dict[str, Any]:
    """Create a CollectionInterface from a dictionary."""
    errs = []
    for collection_type in (ImageInPlate, SingleImage):
        try:
            collection = collection_type.model_validate(data)
            # Remove collection fields from data
            data = {
                k: v for k, v in data.items() if k not in collection_type.model_fields
            }
            data[key_name] = collection
            return data
        except Exception as e:
            errs.append(e)
            continue
    raise ValueError(
        f"Could not create CollectionInterface from data: {data}. Errors: {errs}"
    )
