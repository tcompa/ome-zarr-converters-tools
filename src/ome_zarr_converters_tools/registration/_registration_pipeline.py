from collections.abc import Callable
from typing import Any, TypedDict

from ome_zarr_converters_tools.models._tile_region import TiledImage
from ome_zarr_converters_tools.registration.func import (
    apply_align_to_pixel_grid,
    apply_fov_alignment_corrections,
    apply_mosaic_tiling,
    apply_remove_offsets,
)


class Step(TypedDict):
    name: str
    params: dict[str, Any]


_registration_registry: dict[str, Callable[..., TiledImage]] = {
    "align_to_pixel_grid": apply_align_to_pixel_grid,
    "fov_alignment_corrections": apply_fov_alignment_corrections,
    "remove_offsets": apply_remove_offsets,
    "tile_regions": apply_mosaic_tiling,
}


def add_registration_func(
    function: Callable[..., TiledImage], name: str | None = None
) -> None:
    """Register a new registration step function.

    Args:
        name: Name of the registration step.
        function: Function that performs the registration step.
    """
    if name is None:
        name = function.__name__
    if name in _registration_registry:
        raise ValueError(f"Registration step '{name}' is already registered.")
    _registration_registry[name] = function


def apply_registration_pipeline(
    tiled_image: TiledImage, pipeline_config: list[Step]
) -> TiledImage:
    for step in pipeline_config:
        step_name = step.get("name")
        step_params = step.get("params", {})
        if step_name not in _registration_registry:
            raise ValueError(f"Registration step '{step_name}' is not registered.")
        step_function = _registration_registry[step_name]
        tiled_image = step_function(tiled_image, **step_params)
    return tiled_image


def build_default_registration_pipeline(
    alignment_corrections, tiling_mode
) -> list[Step]:
    return [
        Step(name="remove_offsets", params={}),
        Step(name="align_to_pixel_grid", params={}),
        Step(
            name="fov_alignment_corrections",
            params={"alignment_corrections": alignment_corrections},
        ),
        Step(name="tile_regions", params={"tiling_mode": tiling_mode}),
    ]
