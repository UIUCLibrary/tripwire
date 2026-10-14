"""Speedwagon plugin for Galatea."""

from typing import Dict, Type, Any

import speedwagon.workflow
from uiucprescon.tripwire.speedwagon_workflows import workflows


@speedwagon.hookimpl
def registered_workflows() -> Dict[str, Type[speedwagon.Workflow[Any]]]:
    """Register the workflows used by this plugin."""
    return {
        "Get-Hash": workflows.GetHashWorkflow,
        "validate-checksums": workflows.ValidateChecksumWorkflow,
        "manifest-check": workflows.ManifestCheckWorkflow,
        "metadata-show": workflows.MetadataShowWorkflow,
        "metadata-validate": workflows.MetadataValidateWorkflow
    }
