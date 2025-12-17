"""Models for defining regions to be converted into OME-Zarr format."""

from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class CollectionInterface(BaseModel):
    model_config = ConfigDict(extra="ignore")

    def path(self) -> str:
        raise NotImplementedError("Subclasses must implement path method.")


CollectionInterfaceType = TypeVar("CollectionInterfaceType", bound=CollectionInterface)


class SingleImage(CollectionInterface):
    image_path: str
    suffix: str = ""

    def path(self) -> str:
        return f"{self.image_path}{self.suffix}"


class ImageInPlate(CollectionInterface):
    plate_name: str
    row: str
    column: int = Field(ge=1)
    acquisition: int = Field(default=0, ge=0)
    suffix: str = ""

    @property
    def well(self) -> str:
        return f"{self.row}{self.column}"

    def path_in_well(self) -> str:
        return f"{self.acquisition}{self.suffix}"

    def path(self) -> str:
        return f"{self.row}/{self.column}/{self.path_in_well()}"

    @classmethod
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
