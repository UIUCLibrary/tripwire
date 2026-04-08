"""Introspection utilities."""

from importlib import metadata

__all__ = ["get_application_info"]


def get_application_info() -> str:
    """Get application info."""
    description = get_application_description()
    packages_report = (
        f"\nInstalled Python packages:\n\n{get_install_packages_info()}"
    )
    return "\n".join(list(filter(None, [description, packages_report])))


def get_application_description() -> str:
    return (
        "Tripwire is a tool for validating and processing media manifests. "
        "It is developed by the University of Illinois Urbana-Champaign "
        "Library's Preservation Services Department."
    )


def get_install_packages_info() -> str:
    return "\n".join(
        [
            f"  {x.metadata['Name']}, version: {x.metadata['Version']}"
            for x in sorted(
                metadata.distributions(),
                key=lambda x: x.metadata["Name"].upper(),
            )
        ]
    )
