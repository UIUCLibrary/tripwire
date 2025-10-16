"""UIUC Preservation and Conservation Tripwire Metadata Module.

Added in version 0.3.3
"""

from __future__ import annotations

import abc
import itertools
from collections import defaultdict
import json
from dataclasses import dataclass
import io
import logging
import shutil
import glob as glob_module
import pprint
from typing import (
    Dict,
    Union,
    Callable,
    Iterable,
    Optional,
    List,
    Set,
    TypedDict,
    Literal,
)
import pathlib
import pymediainfo

from uiucprescon.pymediaconch import mediaconch

__all__ = ["show_metadata"]

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


MediaConchRule = TypedDict(
    "MediaConchRule",
    {
        "outcome": Literal["pass", "fail"],
        "requested": str,
        "actual": str,
        "name": str,
    },
)

MediaConchPolicy = TypedDict(
    "MediaConchPolicy",
    {
        "outcome": Literal["pass", "fail"],
        "name": str,
        "rules": List[MediaConchRule],
    },
)

MediaConchMedia = TypedDict(
    "MediaConchMedia",
    {
        "ref": str,
        "policies": List[MediaConchPolicy],
    },
)

MediaConch = TypedDict("MediaConch", {"media": List[MediaConchMedia]})

MediaconchReportData = TypedDict(
    "MediaconchReportData", {"MediaConch": MediaConch}
)


def get_media_metadata(file_path: pathlib.Path) -> Dict[str, Union[str, int]]:
    data = pymediainfo.MediaInfo.parse(file_path)
    return data.to_data()


def get_terminal_width() -> int:
    """Retrieves the terminal width in characters."""
    try:
        # Get the terminal size using shutil.get_terminal_size()
        size = shutil.get_terminal_size()
        return size.columns
    except OSError:
        # Fallback if terminal size cannot be determined (e.g., not a TTY)
        return 80  # Default to 80 columns


def get_console_print_width(terminal_width: int = get_terminal_width()) -> int:
    if terminal_width < 80:
        return 80
    elif terminal_width > 160:
        return 160
    return terminal_width


def generate_metadata_report(
    file: str, metadata, width: int = get_console_print_width()
) -> str:
    report_stream = io.StringIO()
    report_stream.write(f"file: {file}\n\n")
    report_stream.write("metadata: \n")
    pprint.pprint(
        metadata, indent=1, compact=True, width=width, stream=report_stream
    )
    return report_stream.getvalue()


LOCATE_FILE_DEFAULT_FILTERS: List[Callable[[str], bool]] = [
    lambda file_path: pathlib.Path(file_path).is_file(),
]


def locate_files(
    glob_expression: str, filters: Optional[List[Callable[[str], bool]]] = None
) -> Iterable[str]:
    filters = filters if filters is not None else LOCATE_FILE_DEFAULT_FILTERS
    for file_path in glob_module.iglob(glob_expression, recursive=True):
        is_valid = True
        for filter_ in filters:
            if not filter_(file_path):
                is_valid = False
                break
        if is_valid:
            yield file_path


def show_metadata(
    glob: str,
    search_path: pathlib.Path = pathlib.Path("."),
    find_files_strategy: Callable[[str], Iterable[str]] = locate_files,
    get_file_metadata_strategy: Callable[
        [pathlib.Path], Dict[str, Union[str, int]]
    ] = get_media_metadata,
) -> None:
    """Show metadata for files matching the glob pattern."""
    width = get_console_print_width()
    found_some = False
    for file in find_files_strategy(str(search_path / glob)):
        found_some = True
        print("=" * width)
        logger.info(
            generate_metadata_report(
                file,
                metadata=get_file_metadata_strategy(pathlib.Path(file)),
                width=width,
            )
        )
    if found_some:
        print("=" * width)
    else:
        logger.info(f"Found no files matching the pattern: {glob}")


@dataclass
class FileIssues:
    """File issue."""

    file: str
    issues: Set[str]

    def __hash__(self) -> int:
        return hash((self.file, tuple(sorted(self.issues))))


@dataclass
class ValidationResult:
    """Validation result."""

    valid: bool
    files_with_issues: Set[FileIssues]


class AbsValidateStrategy(abc.ABC):
    """Abstract base class for validation strategies."""

    @abc.abstractmethod
    def set_policy_file(self, policy_xml_file: pathlib.Path) -> None:
        """Set the policy file."""

    @abc.abstractmethod
    def validate(self, glob: str) -> ValidationResult:
        """Validate files matching the glob pattern and return a result."""


class MediaConchValidator(AbsValidateStrategy):
    """MediaConch validation strategy."""

    def __init__(self) -> None:
        self.policy_file: Optional[pathlib.Path] = None
        self.issue_formatter: Callable[[MediaConchRule], str] = (
            lambda rule: f'Rule "{rule["name"]}" failed.  '
            f"Expected: {rule['requested']}, "
            f"Got: {rule['actual']}"
        )
        self.mediaconch: Optional[mediaconch.MediaConch] = None
        self.iglob = glob_module.iglob
        self.validate_policy_file: Callable[[pathlib.Path], bool] = (
            lambda policy_xml_file: pathlib.Path(policy_xml_file).is_file()
        )

    def set_policy_file(self, policy_xml_file: pathlib.Path) -> None:
        self.policy_file = policy_xml_file

    @staticmethod
    def _get_media_conch() -> mediaconch.MediaConch:
        mc = mediaconch.MediaConch()
        mc.set_format(mediaconch.MediaConch_format_t.MediaConch_format_Json)
        return mc

    @staticmethod
    def _parse_media_conch_report(
        report_data: MediaconchReportData,
    ) -> List[MediaConchMedia]:
        return report_data["MediaConch"]["media"]

    def _iter_failing_rules(
        self, policies: List[MediaConchPolicy]
    ) -> Iterable[str]:
        for policy in policies:
            if policy["outcome"] != "pass":
                for rule in policy.get("rules", []):
                    if rule["outcome"] != "pass":
                        yield self.issue_formatter(rule)

    def validate(self, glob: str) -> ValidationResult:
        if not self.policy_file:
            raise ValueError("Policy file must be set before validation.")

        mc = self.mediaconch or self._get_media_conch()
        if not self.validate_policy_file(self.policy_file):
            raise ValueError("Policy file must be valid policy file.")
        mc.add_policy(str(self.policy_file))

        files_with_issues = set()

        for file in self.iglob(glob, recursive=True):
            print(f"validating {file}")
            result: MediaconchReportData = json.loads(
                mc.get_report(mc.add_file(str(file)))
            )
            file_is_valid = True
            for item in self._parse_media_conch_report(result):
                assert item["ref"] == str(file), (
                    f"Expected {item['ref']} to be {file}"
                )
                failing_rules = set(self._iter_failing_rules(item["policies"]))
                if failing_rules:
                    file_is_valid = False
                files_with_issues.add(
                    FileIssues(file=file, issues=failing_rules)
                )

            if not file_is_valid:
                logger.error(f"validating {file}: Fail")
            else:
                logger.info(f"validating {file}: Pass")

        return ValidationResult(
            valid=len(files_with_issues) > 0,
            files_with_issues=files_with_issues,
        )


class ValidationReportBuilder:
    def __init__(self) -> None:
        super().__init__()
        self.file_issues: Dict[str, Set[str]] = defaultdict(set)

    def add_file_issue(self, file_name: str, issue: str) -> None:
        self.file_issues[file_name].add(issue)

    def build_report(self) -> str:
        header = """
==================
Validation Results
==================
""".strip()
        sections: List[str] = []
        for file_name, issues in self.file_issues.items():
            issues_string = "\n".join([f"  {i}" for i in issues])
            report_string = f"File: {file_name} \nIssues:\n {issues_string}"
            sections.append(report_string)
        sections_string = "\n".join(sections)
        if len(sections_string) > 0:
            return f"{header}\n\n{sections_string}"
        return f"{header}\n\nNo issues found."


def validate_metadata(
    glob: str,
    policy_xml_file: pathlib.Path,
    validate_strategy: AbsValidateStrategy = MediaConchValidator(),
) -> bool:
    """Validate metadata for files matching the glob pattern.

    Args:
        glob: Glob pattern to match files.
        policy_xml_file: MediaConch policy XML file.
        validate_strategy: class implementing AbsValidateStrategy

    Returns:
        If all files pass validation, returns True. If any file fails
        validation, returns False.

    """
    validate_strategy.set_policy_file(policy_xml_file)
    result = validate_strategy.validate(glob)

    # Create a report of issues
    report_builder = ValidationReportBuilder()
    for file_name, file_results in itertools.groupby(
        result.files_with_issues, key=lambda i: i.file
    ):
        for file_result in file_results:
            for issue in file_result.issues:
                report_builder.add_file_issue(file_name, issue)
    logger.info(report_builder.build_report())

    return result.valid
