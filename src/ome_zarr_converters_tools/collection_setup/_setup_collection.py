"""Collection setup functions for OME-Zarr converters tools."""

from collections.abc import Mapping
from typing import Any, ParamSpec, Protocol

from zarr.abc.store import Store

from ome_zarr_converters_tools.models._collection import (
    ImageInPlate,
    SingleImage,
)
from ome_zarr_converters_tools.models._tile_region import TiledImage


def setup_plates(
    store: Store,
    tiled_image: list[TiledImage],
    ngff_version: str = "0.5",
) -> None:
    """Set up an ImageInPlate collection in the Zarr group."""
    assert isinstance(tiled_image[0].collection, ImageInPlate)
    raise NotImplementedError("Plate setup is not yet implemented.")


def setup_single_image(
    store: Store,
    tiled_image: list[TiledImage],
    ngff_version: str = "0.5",
) -> None:
    """Set up a SingleImage collection in the Zarr group."""
    assert isinstance(tiled_image[0].collection, SingleImage)
    raise NotImplementedError("Single image setup is not yet implemented.")


P = ParamSpec("P")


class SetupCollectionFunction(Protocol[P]):
    """Protocol for collection setup handler functions.

    The function is responsible for setting up the collection structure
    in the zarr store, and creating any necessary metadata.
    """

    __name__: str

    def __call__(
        self,
        store: Store,
        tiled_image: list[TiledImage],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        """Set up the collection in the Zarr store."""
        ...


_collection_handler_registry: dict[str, SetupCollectionFunction] = {
    "SingleImage": setup_single_image,
    "ImageInPlate": setup_plates,
}


def add_collection_handler(
    function: SetupCollectionFunction,
    name: str | None = None,
    overwrite: bool = False,
) -> None:
    """Register a new collection setup handler.

    The collection setup handler is responsible for setting up the
    collection structure and metadata in the Zarr group.

    Args:
        name: Name of the collection setup handler. By convention,
            the name of the CollectionInterfaceType,
            e.g., 'SingleImage' or 'ImageInPlate'.
        function: Function that performs the collection setup step.
        overwrite: Whether to overwrite an existing collection setup step
            with the same name.
    """
    if name is None:
        name = function.__name__
    if not overwrite and name in _collection_handler_registry:
        raise ValueError(f"Collection setup handler '{name}' is already registered.")
    _collection_handler_registry[name] = function


def setup_collection(
    store: Store,
    tiles: list[TiledImage],
    handler_type: str,
    **collection_handler_config: Mapping[str, Any],
) -> None:
    """Set up the collection in the Zarr group using the specified handler.

    Args:
        store: Store to set up the collection in.
        tiles: List of TiledImage to set up the collection for.
        handler_type: Type of the collection setup handler to use.
        collection_handler_config: Configuration for the collection setup handler.
            Must contain the key 'type' with the name of the registered
            collection setup handler.

    Returns:
        The list of TiledImage after applying the collection setup handler.
    """
    handler_function = _collection_handler_registry.get(handler_type)
    if handler_function is None:
        raise ValueError(
            f"Collection setup handler '{handler_type}' is not registered."
        )
    return handler_function(store, tiles, **collection_handler_config)
