"""Speedwagon workflows."""

import logging
import os
import pathlib
import pprint
from typing import (
    List,
    Mapping,
    Any,
    Sequence,
    TypeVar,
    Optional,
    Callable,
    Set,
)

import uiucprescon
from speedwagon import Workflow
from speedwagon.tasks import Result, TaskBuilder
import speedwagon.workflow
from speedwagon.validators import JobOptionsType
from speedwagon.workflow import AbsOutputOptionDataType
import speedwagon.validators

from uiucprescon.tripwire import validation, metadata, manifest_check

__all__ = [
    "GetHashWorkflow",
    "ManifestCheckWorkflow",
    "MetadataShowWorkflow",
    "MetadataValidateWorkflow",
    "ValidateChecksumWorkflow",
]

_T = TypeVar("_T", bound=Mapping[str, object])

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RedirectHandler(logging.Handler):
    """Logging handler that redirects logging to another logger."""

    def __init__(self, target_logger: logging.Logger, level: int = 0):
        super().__init__(level)
        self.target_logger = target_logger

    def emit(self, record):
        self.target_logger.handle(record)


def get_hash_and_report(
    file_path: str,
    hashing_algorithm: str,
    hash_strategy=validation.get_file_hash_with_progress_reporting,
    report_logger=logger,
) -> str:
    def progress_reporter(value):
        if value < 100:
            report_logger.info("Progress %s", value)
        else:
            report_logger.info("Hashing complete")

    return hash_strategy(
        pathlib.Path(file_path),
        hashing_algorithm=validation.SUPPORTED_ALGORITHMS[hashing_algorithm],
        progress_reporter=progress_reporter,
    )


@speedwagon.tasks.tasks.workflow_task("Hash File", logger=logger)
def hash_file_task(file_path, hashing_algorithm, strategy=get_hash_and_report):
    logger.info(
        "Calculating hash for %s using %s algorithm",
        file_path,
        hashing_algorithm,
    )
    return {"file": file_path, "hash": strategy(file_path, hashing_algorithm)}


class GetHashWorkflow(Workflow):
    """Get hash workflow.

    This is the equivalent of the command line command "tripwire get-hash".

    """

    name = "Get-Hash"

    def job_options(self) -> List[speedwagon.workflow.AbsOutputOptionDataType]:
        """Job options for getting checksum hash workflow.

        Returns:
            list of job options
        """
        hashing_algo = speedwagon.workflow.ChoiceSelection(
            label="Hashing Algorithm"
        )
        for k in validation.SUPPORTED_ALGORITHMS.keys():
            hashing_algo.add_selection(k)
        hashing_algo.default_value = "md5"
        options = [speedwagon.workflow.FileSelectData("File"), hashing_algo]

        return options

    def discover_task_metadata(
        self,
        initial_results: List[Result],
        additional_data: Mapping[str, Any],
        user_args: _T,
    ) -> Sequence[Mapping[str, object]]:
        """Discovers metadata for getting the md5 checksum.

        Args:
            initial_results: initial results
            additional_data: additional data
            user_args: user arguments

        Returns:
            sequence of task metadata
        """
        return [user_args]

    def create_new_task(self, task_builder: TaskBuilder, job_args) -> None:
        """Creates a new task to get checksum hash.

        Args:
            task_builder: task builder
            job_args: job arguments

        """
        task_builder.add_subtask(
            hash_file_task(
                file_path=job_args["File"],
                hashing_algorithm=job_args["Hashing Algorithm"],
            )
        )

    @classmethod
    def generate_report(
        cls, results: List[Result], user_args: _T
    ) -> Optional[str]:
        """Generate report.

        Args:
            results: results of the hash generation task
            user_args: user arguments

        Returns:
            Report str
        """
        reported_content = []
        for result in results:
            algorithm = user_args["Hashing Algorithm"]
            reported_content.append(
                f"{result.data['file']} -> {algorithm}: {result.data['hash']}"
            )
        report = "\n".join(["Results:"] + reported_content)
        return report


@speedwagon.tasks.tasks.workflow_task("Validate Checksums", logger=logger)
def validate_checksums_task(
    file_path,
    log_level: int = logging.INFO,
    validate_directory_strategy=validation.validate_directory_checksums_command,
):
    logger.info("Validating checksums for %s", file_path)
    handler = RedirectHandler(logger, level=log_level)
    try:
        validation.logger.addHandler(handler)
        validate_directory_strategy(pathlib.Path(file_path))
    finally:
        validation.logger.removeHandler(handler)
    logger.info("Done")


class ValidateChecksumWorkflow(Workflow):
    """Validate checksum workflow.

    This is the equivalent of the "tripwire validate-checksums" command.
    """

    name = "validate-checksums"

    def discover_task_metadata(
        self,
        initial_results: List[Result],
        additional_data: Mapping[str, Any],
        user_args: _T,
    ) -> Sequence[Mapping[str, object]]:
        """Discovers metadata for the validing checksums task.

        Args:
            initial_results: initial results
            additional_data: additional data
            user_args: user arguments

        Returns:
            sequence of task metadata
        """
        return [{"path": user_args["path"]}]

    def job_options(self) -> List[AbsOutputOptionDataType]:
        """Job options for validating checksums workflow.

        Returns:
            list of job options
        """
        options: List[AbsOutputOptionDataType] = [
            speedwagon.workflow.DirectorySelect("path"),
        ]
        return options

    def create_new_task(self, task_builder: TaskBuilder, job_args) -> None:
        """Creates a new task to check checksums.

        Args:
            task_builder: task builder
            job_args: job arguments

        """
        task_builder.add_subtask(validate_checksums_task(job_args["path"]))


class ManifestCheckWorkflow(Workflow):
    """Manifest check workflow.

    This is the equivalent of the "tripwire manifest-check" command.
    """

    name = "manifest-check"

    def create_new_task(self, task_builder: TaskBuilder, job_args) -> None:
        super().create_new_task(task_builder, job_args)

    # active = False
    # TODO: implement manifest-check workflow

    def discover_task_metadata(
        self,
        initial_results: List[Result],
        additional_data: Mapping[str, Any],
        user_args: _T,
    ) -> Sequence[Mapping[str, object]]:
        """Discovers metadata for the manifest checking task.

        Args:
            initial_results: initial results
            additional_data: additional data
            user_args: user arguments

        Returns:
            sequence of task metadata
        """
        return [
            {
                "manifest": user_args["Manifest tsv File"],
                "search_path": user_args["Search Path"],
            }
        ]

    def job_options(self) -> List[AbsOutputOptionDataType]:
        """Job options for manifest check workflow.

        Returns:
            list of job options
        """
        manifest_tsv_file = speedwagon.workflow.FileSelectData(
            "Manifest tsv File"
        )
        search_path = speedwagon.workflow.DirectorySelect("Search Path")
        return [manifest_tsv_file, search_path]


@speedwagon.tasks.workflow_task(
    "Locate Files in Manifest", logger=manifest_check.logger
)
def locate_manifest_files_task(manifest_tsv_file: str, search_path: str):
    manifest_check.locate_manifest_files(
        pathlib.Path(manifest_tsv_file), pathlib.Path(search_path)
    )


@speedwagon.tasks.workflow_task("Show Metadata", logger=logger)
def show_metadata_task(
    file_path: str, get_metadata_strategy=metadata.get_media_metadata
):
    logger.info("Processing file: %s", file_path)
    result = get_metadata_strategy(pathlib.Path(file_path))
    return {"file": file_path, "result": result}


class MetadataShowWorkflow(Workflow):
    """Metadata show workflow.

    This is the equivalent of the "tripwire metadata show" command.
    """

    name = "metadata-show"

    locate_files_strategy = lambda _, glob: metadata.locate_files(glob)  # noqa: E731

    def discover_task_metadata(
        self,
        initial_results: List[Result],
        additional_data: Mapping[str, Any],
        user_args: _T,
    ) -> Sequence[Mapping[str, object]]:
        """Discovers metadata for the metadata show tasks.

        Args:
            initial_results: initial results
            additional_data: additional data
            user_args: user arguments

        Returns:
            sequence of task metadata
        """
        files = list(self.locate_files_strategy(user_args["glob"]))
        if len(files) == 0:
            logger.warning("No files found matching the glob pattern.")
            return []
        return [{"file": f} for f in files]

    def job_options(self) -> List[AbsOutputOptionDataType]:
        """Job options for showing metadata.

        Returns:
            list of job options
        """
        glob = speedwagon.workflow.TextLineEditData("glob")
        return [glob]

    def create_new_task(self, task_builder: TaskBuilder, job_args) -> None:
        """Creates a new task to show metadata.

        Args:
            task_builder: task builder
            job_args: job arguments

        """
        file_path = job_args.get("file")
        if file_path is None:
            logger.warning("No file path provided.")
            return
        task_builder.add_subtask(show_metadata_task(file_path=file_path))

    @classmethod
    def generate_report(
        cls, results: List[Result], user_args: _T
    ) -> Optional[str]:
        """Generate report.

        Args:
            results: results of the metadata show task
            user_args: user arguments

        Returns:
            Report str
        """
        report_lines = []
        for result in results:
            report_lines.append(f"File: {result.data['file']}")
            report_lines.append(pprint.pformat(result.data["result"]))
        report = "\n".join(report_lines)
        return report


def valid_glob_with_mediaconch(
    policy_file: pathlib.Path,
    glob_expression: str,
    validator_strategy=uiucprescon.tripwire.metadata.MediaConchValidator,
) -> bool:
    trip_wire_validator = validator_strategy()
    trip_wire_validator.policy_file = policy_file
    return trip_wire_validator.validate(glob_expression).valid


class IsMediaConchPoliceFile(speedwagon.validators.AbsOutputValidation):
    get_policy_file_issues_strategy = (  # noqa: E731
        lambda self,
        fp: uiucprescon.tripwire.metadata.find_mediaconch_policy_file_issues(
            fp
        )
    )

    def __init__(self) -> None:
        super().__init__()
        self.checks: List[Callable[[pathlib.Path], Set[str]]] = [
            self.get_policy_file_issues
        ]

    def get_policy_file_issues(self, file_path: pathlib.Path) -> Set[str]:
        if not file_path.exists():
            return {"Find not found"}
        with file_path.open() as fp:
            return self.get_policy_file_issues_strategy(fp)

    def investigate(self, candidate, job_options: JobOptionsType) -> List[str]:
        if candidate is None or str(candidate).strip() == "":
            return ["Invalid policy file path"]
        issues: Set[str] = set()
        for check in self.checks:
            issues = issues.union(check(pathlib.Path(candidate)))
        return list(issues)


class MediaConchValidateGlobString(speedwagon.validators.AbsOutputValidation):
    validator_strategy: Callable[[pathlib.Path, str], bool] = (
        lambda policy_file, glob_expression: valid_glob_with_mediaconch(
            policy_file, glob_expression
        )
    )

    def investigate(self, candidate, job_options: JobOptionsType) -> List[str]:
        if candidate is None or str(candidate).strip() == "":
            return [f'"{candidate}" is not a valid glob expression']

        policy_file = job_options["Policy File"] = job_options.get(
            "Policy File"
        )
        if policy_file is None:
            return [
                "Unable to validate without a policy file set in job options"
            ]
        if not MediaConchValidateGlobString.validator_strategy(
            pathlib.Path(policy_file), candidate
        ):
            return [f'"{candidate}" is not a valid glob expression']
        return []


class MetadataValidateWorkflow(Workflow):
    """Metadata validation workflow.

    This is the equivalent of the "tripwire metadata validate" command.
    """

    name = "metadata-validate"

    def discover_task_metadata(
        self,
        initial_results: List[Result],
        additional_data: Mapping[str, Any],
        user_args: _T,
    ) -> Sequence[Mapping[str, object]]:
        """Discovers metadata for the validation task.

        Args:
            initial_results: initial results
            additional_data: additional data
            user_args: user arguments

        Returns:
            sequence of task metadata
        """
        return [
            {
                "policy_file": user_args["Policy File"],
                "glob": user_args["glob"],
            }
        ]

    def job_options(self) -> List[AbsOutputOptionDataType]:
        """Job options for metadata validation workflow.

        Returns:
            list of job options
        """
        glob = speedwagon.workflow.TextLineEditData("glob")
        glob.add_validation(
            MediaConchValidateGlobString(),
            condition=lambda _, job_args: os.path.exists(
                str(job_args.get("Policy File", ""))
            ),
        )

        policy_file = speedwagon.workflow.FileSelectData("Policy File")
        policy_file.add_validation(speedwagon.validators.ExistsOnFileSystem())
        policy_file.add_validation(
            IsMediaConchPoliceFile(),
            condition=lambda value, _: os.path.exists(value),
        )
        return [policy_file, glob]

    def create_new_task(self, task_builder: TaskBuilder, job_args) -> None:
        """Creates a new task to validate metadata.

        Args:
            task_builder: task builder
            job_args: job arguments

        """
        task_builder.add_subtask(
            validate_metadata_task(job_args["policy_file"], job_args["glob"])
        )


@speedwagon.tasks.workflow_task("Validate Metadata", logger=metadata.logger)
def validate_metadata_task(
    policy_file: str,
    glob: str,
    validate_metadata_strategy=metadata.validate_metadata,
):
    validate_metadata_strategy(glob, pathlib.Path(policy_file))
