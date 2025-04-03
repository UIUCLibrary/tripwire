"""File handling for files used by tripwire."""

import abc
import collections
import csv
import dataclasses
import functools
import logging
import typing
from enum import Enum
from functools import cached_property
from typing import (
    NamedTuple,
    overload,
    TextIO,
    Iterator,
    Mapping,
    TypeVar,
    Sequence,
    Union,
    ParamSpec,
    Callable,
    Set,
    Type,
)

from typing import Final

__all__ = ["TSVManifest"]

T = TypeVar("T")
P = ParamSpec("P")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class InvalidFileFormat(Exception):
    """Invalid file format exception."""

    def __init__(self, file: str = "", details="") -> None:
        message = (
            f"Invalid file format. File: {file}"
            if file
            else "Invalid file format"
        )
        if details:
            message = f"{message}. Details: {details}"
        super().__init__(message)
        self.file_name = file
        self.details = details


@dataclasses.dataclass(frozen=True)
class TableRow:
    """Table row."""

    line_number: int
    row_data: Mapping[str, str]

    def __getitem__(self, key: str) -> str:
        """Get item by key."""
        return self.row_data[key]


def remembered_file_pointer(func: Callable[P, T]) -> Callable[P, T]:
    """Decorator to return the file pointer to the position it started at."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        fp: TextIO = typing.cast(TextIO, kwargs["fp"])
        starting = fp.tell()
        try:
            return func(*args, **kwargs)
        finally:
            fp.seek(starting)

    return wrapper


class ValidationFindingLevel(Enum):
    """Validation levels."""

    NONE = 0
    WARNING = 1
    ERROR = 2


class Finding(NamedTuple):
    """Validation finding."""

    level: ValidationFindingLevel
    message: str


class AbsFileValidator(abc.ABC):
    def __init__(self, fp: TextIO) -> None:
        self.fp = fp

    @abc.abstractmethod
    def get_validation_findings(self) -> Set[Finding]:
        """Subclasses should implement this method for validation.

        Returns:
            List of validation findings.
        """


class SupportedFileTypes(Enum):
    MANIFEST_TSV = "manifest_tsv"


INVALID_MANIFEST_TSV_ERROR_MESSAGE = (
    "Data in file is not in a valid manifest format"
)


def discover_manifest_tsv_findings(fp: TextIO) -> Set[Finding]:
    findings: Set[Finding] = set()
    try:
        next(csv.DictReader(fp, dialect="excel-tab"))
    except StopIteration:
        # No rows in the file.
        findings.add(
            Finding(ValidationFindingLevel.WARNING, "No rows in the file.")
        )

    except (csv.Error, UnicodeDecodeError):
        # Something funky with the file. Probably not a TSV file.
        findings.add(
            Finding(
                ValidationFindingLevel.ERROR,
                INVALID_MANIFEST_TSV_ERROR_MESSAGE,
            )
        )
    return findings


class ManifestTSVAbsFileValidator(AbsFileValidator):
    validations: Sequence[Callable[[TextIO], Set[Finding]]] = [
        discover_manifest_tsv_findings
    ]

    def get_validation_findings(self) -> Set[Finding]:
        findings: Set[Finding] = set()
        for validation in self.validations:
            validation_findings = validation(self.fp)
            if validation_findings:
                findings = findings.union(validation_findings)
        return findings


DEFAULT_FILE_VALIDATORS: Final[
    Mapping[SupportedFileTypes, Type[AbsFileValidator]]
] = {
    SupportedFileTypes.MANIFEST_TSV: ManifestTSVAbsFileValidator,
}


def find_validator_factory(
    fp: TextIO, file_type: SupportedFileTypes
) -> AbsFileValidator:
    try:
        return DEFAULT_FILE_VALIDATORS[file_type](fp)
    except KeyError:
        raise ValueError(f"No validator available for file type: {file_type}")


class _TSVManifestReader:
    reader = functools.partial(csv.DictReader, dialect="excel-tab")
    get_validator = find_validator_factory

    @classmethod
    @remembered_file_pointer
    def iter_over_file_pointer(cls, fp: TextIO) -> Iterator[TableRow]:
        """Iterate over the file pointer."""
        reader = cls.reader(fp)
        for row in reader:
            yield TableRow(line_number=reader.line_num, row_data=row)

    @classmethod
    @remembered_file_pointer
    def get_items(
        cls, fp: TextIO, index: Union[int, slice]
    ) -> Union[TableRow, Sequence[TableRow]]:
        reader = cls.reader(fp)
        return [
            TableRow(line_number=reader.line_num, row_data=row)
            for row in reader
        ][index]

    @classmethod
    @remembered_file_pointer
    def get_total_entries(cls, fp: TextIO) -> int:
        return len(list(cls.reader(fp)))

    @classmethod
    @remembered_file_pointer
    def is_valid_file(cls, fp: TextIO) -> bool:
        """Check if the file is a valid TSV file."""
        validator = cls.get_validator(fp, SupportedFileTypes.MANIFEST_TSV)
        findings = validator.get_validation_findings()
        is_valid = True
        if findings:
            for finding in findings:
                match finding.level:
                    case ValidationFindingLevel.WARNING:
                        logger.warning(finding.message)
                    case ValidationFindingLevel.ERROR:
                        logger.error(finding.message)
                        is_valid = False
                    case _:
                        logger.warning(
                            (
                                "Unknown validation level. "
                                'level: %s. message: "%s"'
                            ),
                            finding.level,
                            finding.message,
                        )
        return is_valid


class TSVManifest(collections.abc.Sequence[TableRow]):
    """A class to handle TSV manifest files."""

    def __init__(self, fp: TextIO) -> None:
        """Create a TSVManifest object."""
        self._fp = fp
        self._tsv_manifest = _TSVManifestReader()

    def __iter__(self) -> Iterator[TableRow]:
        """Iterate over the TSV file contents."""
        return self._tsv_manifest.iter_over_file_pointer(fp=self._fp)

    @cached_property
    def total_entries(self) -> int:
        """Get the number of entries in the TSV file."""
        return self._tsv_manifest.get_total_entries(fp=self._fp)

    def __len__(self) -> int:
        """Get the number of entries in the TSV file."""
        return self.total_entries

    @overload
    def __getitem__(self, index: int) -> TableRow: ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[TableRow]: ...

    def __getitem__(
        self, index: Union[int, slice]
    ) -> Union[TableRow, Sequence[TableRow]]:
        """Get item by index.

        Note: The index is the determined by order of the record in the file,
        and not the line number it is on.
        """
        if isinstance(index, slice):
            max_size = len(self)
            if index.start < 0 or index.stop > max_size:
                raise IndexError("out of bounds")
        else:
            if index >= len(self):
                raise IndexError("out of bounds")
        return self._tsv_manifest.get_items(fp=self._fp, index=index)

    def is_valid_file(self) -> bool:
        """Check if the file is a valid manifest TSV file."""
        return self._tsv_manifest.is_valid_file(fp=self._fp)
