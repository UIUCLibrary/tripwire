"""General utility library functions."""

import importlib
import pathlib
from typing import Optional, Callable, Iterable, List, cast
from importlib.metadata import version
import tomllib

__all__ = ["get_version"]


class InvalidVersionStrategy(Exception):
    pass


class MissingVersionInformation(Exception):
    pass


def get_package_version() -> str:
    try:
        return version(__package__)
    except importlib.metadata.PackageNotFoundError as error:
        raise InvalidVersionStrategy(
            "package metadata not installed"
        ) from error


def get_version_from_pyproject(
    path: pathlib.Path = (
        pathlib.Path(__file__).parent / ".." / "pyproject.toml"
    ).resolve(),
) -> str:
    if not path.is_file():
        raise InvalidVersionStrategy("pyproject.toml not found")
    with path.open("rb") as f:
        pyproject_toml = tomllib.load(f)
        try:
            return cast(str, pyproject_toml["project"]["version"])
        except KeyError as error:
            raise InvalidVersionStrategy(
                "pyproject.toml does not contain a version"
            ) from error


DEFAULT_VERSION_RESOLUTION_STRATEGY_ORDER: List[Callable[[], str]] = [
    get_package_version,
    get_version_from_pyproject,
]


def get_version(
    resolution_order: Optional[Iterable[Callable[[], str]]] = None,
) -> str:
    """Get current version of this code.

    Args:
        resolution_order: List of callable functions that either return a
            version string or raise an InvalidVersionStrategy.

    Returns: a version string or raise an MissingVersionInformation exception.

    """
    if resolution_order is None:
        resolution_order = DEFAULT_VERSION_RESOLUTION_STRATEGY_ORDER

    for strategy in resolution_order:
        try:
            return strategy()
        except InvalidVersionStrategy:
            pass

    raise MissingVersionInformation("Unable to determine package version")
