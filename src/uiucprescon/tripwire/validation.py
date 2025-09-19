"""Validation module for checksum files."""

import hashlib
import io
import os
import pathlib
from typing import (
    Any,
    BinaryIO,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Protocol,
    TextIO,
)
from uiucprescon.tripwire.files import remembered_file_pointer
import logging

from tqdm import tqdm

__all__ = ["validate_directory_checksums_command"]


SUPPORTED_ALGORITHMS = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_hash_from_file_pointer(
    pointer: BinaryIO,
    hashing_algorithm,
    progress_reporter: Optional[Callable[[float], None]] = None,
) -> str:
    """Calculates the hash of a given file pointer.

    Args:
        pointer: file pointer
        hashing_algorithm: hashing algorithm to use such as hashlib.md5
        progress_reporter: callback to a function that reports progress

    Returns: hash value

    """
    item_hash = hashing_algorithm()
    starting_point = pointer.tell()
    pointer.seek(0, io.SEEK_END)
    size = pointer.tell() - starting_point
    pointer.seek(starting_point)
    while chunk := pointer.read(item_hash.block_size * 128):
        item_hash.update(chunk)
        if progress_reporter:
            progress_from_start = pointer.tell() - starting_point
            progress = progress_from_start / size * 100
            progress_reporter(progress)
    return item_hash.hexdigest()


def get_file_hash_with_progress_reporting(
    path: pathlib.Path,
    hashing_algorithm,
    progress_reporter: Optional[Callable[[float], None]] = None,
    hashing_strategy: Callable[
        [BinaryIO, Any, Optional[Callable[[float], None]]], str
    ] = get_hash_from_file_pointer,
) -> str:
    """Gets hash value for a file.

    Args:
        path: file path
        hashing_algorithm: hashing algorithm to use such as hashlib.md5
        progress_reporter: callback to a function that reports progress
        hashing_strategy: strategy to use for hashing

    Returns: hash value

    """
    with path.open("rb") as file:
        return hashing_strategy(file, hashing_algorithm, progress_reporter)


class GetFileHashStrategyProtocol(Protocol):
    def __call__(
        self,
        path: pathlib.Path,
        hashing_algorithm,
        progress_reporter: Optional[Callable[[float], None]],
        hashing_strategy: Callable[
            [BinaryIO, Any, Optional[Callable[[float], None]]], str
        ],
    ) -> str: ...


def validate_file_against_expected_hash(
    expected_hash: str,
    target_file: pathlib.Path,
    get_file_hash_strategy: GetFileHashStrategyProtocol = get_file_hash_with_progress_reporting,  # noqa: E501
) -> Optional[List[str]]:
    prog_bar_format = (
        "{desc}{percentage:3.0f}% |{bar}| Time Remaining: {remaining}"
    )
    progress_bar = ProgressBar(
        total=100.0, leave=False, bar_format=prog_bar_format
    )
    progress_bar.set_description("Calculating hash")
    hash_value = get_file_hash_strategy(
        path=target_file,
        hashing_algorithm=hashlib.md5,
        progress_reporter=lambda value,  # type: ignore[misc]
        prog_bar=progress_bar: prog_bar.set_progress(value),
        hashing_strategy=get_hash_from_file_pointer,
    )

    progress_bar.close()
    if expected_hash.lower() != hash_value.lower():
        return [
            f"Hash mismatch. Expected: {expected_hash}. Actual: {hash_value}"
        ]
    return None


class ProgressBar(tqdm):
    def __init__(self, total, *args, **kwargs):
        super().__init__(total, *args, **kwargs)
        self.total = total

    def set_progress(self, position: float) -> None:
        if self.n < position:
            self.update(position - self.n)
        elif self.n > position:
            self.n = position
            self.update(0)
        if position == self.total:
            self.refresh()


def locate_checksum_files(path: pathlib.Path) -> Iterable[pathlib.Path]:
    for root, dirs, files in os.walk(path):
        for file_name in files:
            if not file_name.endswith(".md5"):
                continue
            yield pathlib.Path(os.path.join(root, file_name))


def get_hash_command(
    files: List[pathlib.Path], hashing_algorithm: str
) -> None:
    prog_bar_format = (
        "{desc}{percentage:3.0f}% |{bar}| Time Remaining: {remaining}"
    )

    for i, file_path in enumerate(files):
        progress_bar = ProgressBar(
            total=100.0, leave=False, bar_format=prog_bar_format
        )

        progress_bar.set_description(file_path.name)
        result = get_file_hash_with_progress_reporting(
            file_path,
            hashing_algorithm=SUPPORTED_ALGORITHMS[hashing_algorithm],
            progress_reporter=lambda value,  # type: ignore[misc]
            prog_bar=progress_bar: prog_bar.set_progress(value),
        )
        progress_bar.close()

        # Report the results
        if len(files) == 1:
            pre_fix = ""
        else:
            pre_fix = f"({i + 1}/{len(files)}) "
        logger.info(f"{pre_fix}{file_path} --> {hashing_algorithm}: {result}")


def create_checksum_validation_report(
    checksum_files_checked: List[pathlib.Path], errors: List[str]
) -> str:
    report_header = "Results:"

    if errors:
        report_error_list = "\n".join([f" * {e}" for e in errors])
        report_body = f"""The following files failed:
    {report_error_list}
    """
    else:
        report_body = f"All {len(checksum_files_checked)} checksum(s) matched."

    return f"""{report_header}

    {report_body}
    """


def read_hash_and_file_format(fp: TextIO) -> str:
    starting = fp.tell()
    try:
        fp.seek(0)
        results = fp.read()
        return results.split(" ")[0]
    finally:
        fp.seek(starting)


def read_hash_only_format(fp: TextIO) -> str:
    starting = fp.tell()
    try:
        fp.seek(0)
        return fp.read().strip()
    finally:
        fp.seek(starting)


checksum_reading_strategies: Dict[str, Callable[[TextIO], str]] = {
    "hash_and_file": read_hash_and_file_format,
    "only_hash_value": read_hash_only_format,
}


@remembered_file_pointer
def get_checksum_file_reading_strategy(fp: TextIO) -> Callable[[TextIO], str]:
    fp.seek(0)
    data = fp.read()
    results = data.split()
    if len(results) == 1:
        return checksum_reading_strategies["only_hash_value"]
    return checksum_reading_strategies["hash_and_file"]


def read_checksum_file(file_path: pathlib.Path) -> str:
    with file_path.open("r") as f:
        return get_checksum_file_reading_strategy(fp=f)(f)


def validate_directory_checksums_command(
    path: pathlib.Path,
    locate_checksum_strategy: Callable[
        [pathlib.Path], Iterable[pathlib.Path]
    ] = locate_checksum_files,
    read_checksums_strategy: Callable[
        [pathlib.Path], str
    ] = read_checksum_file,
    compare_checksum_to_target_strategy: Callable[
        [str, pathlib.Path], Optional[List[str]]
    ] = validate_file_against_expected_hash,
) -> None:
    """Validate checksum files located inside the directory.

    Args:
        path: path to directory containing checksums and matching files
        locate_checksum_strategy: strategy to locate checksum files
        read_checksums_strategy: strategy to read checksum files
        compare_checksum_to_target_strategy: strategy to compare checksum files

    """
    logger.info("Locating checksums files...")
    checksum_files = list(locate_checksum_strategy(path))
    logger.info("Validating checksums...")
    errors = []
    for i, checksum_file in enumerate(checksum_files):
        expected_hash_value = read_checksums_strategy(checksum_file)

        target_file = pathlib.Path(
            os.path.join(
                checksum_file.parent, checksum_file.name.replace(".md5", "")
            )
        )
        logger.info(
            "(%d/%d) Validating %s",
            i + 1,
            len(checksum_files),
            target_file.relative_to(path),
        )
        issues = compare_checksum_to_target_strategy(
            expected_hash_value, target_file
        )
        if issues:
            file_report = ", ".join(issues)
            message = (
                f"{target_file.relative_to(path)} - Failed: {file_report}"
            )
            logger.error(message)
            errors.append(message)
        else:
            logger.info("%s - Checksum matched", target_file.relative_to(path))

    logger.info("Job done!")
    logger.info(
        create_checksum_validation_report(
            checksum_files_checked=checksum_files, errors=errors
        )
    )
