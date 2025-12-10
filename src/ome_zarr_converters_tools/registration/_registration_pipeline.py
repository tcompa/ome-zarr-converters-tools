from collections.abc import Callable
from typing import Any, TypedDict

from ome_zarr_converters_tools.models._tile_region import TiledImage
from ome_zarr_converters_tools.registration.func import align_regions, tile_regions


class Step(TypedDict):
    name: str
    params: dict[str, Any]


_registry: dict[str, Callable[..., TiledImage]] = {
    "align_regions": align_regions,
    "tile_regions": tile_regions,
}


def add_registration_func(name: str, function: Callable[..., TiledImage]) -> None:
    """Register a new registration step function.

    Args:
        name: Name of the registration step.
        function: Function that performs the registration step.
    """
    if name in _registry:
        raise ValueError(f"Registration step '{name}' is already registered.")
    _registry[name] = function


def apply_registration_pipeline(
    tiled_image: TiledImage, pipeline_config: list[Step]
) -> TiledImage:
    for step in pipeline_config:
        step_name = step.get("name")
        step_params = step.get("params", {})
        if step_name not in _registry:
            raise ValueError(f"Registration step '{step_name}' is not registered.")
        step_function = _registry[step_name]
        tiled_image = step_function(tiled_image, **step_params)
    return tiled_image


def build_default_registration_pipeline(
    alignment_corrections, tiling_mode
) -> list[Step]:
    return [
        Step(
            name="align_regions",
            params={"alignement_corrections": alignment_corrections},
        ),
        Step(name="tile_regions", params={"tiling_mode": tiling_mode}),
    ]
