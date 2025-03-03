import hashlib
import io
import os
import pathlib
from typing import BinaryIO, Optional, Callable, Any, List, Iterable
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


def get_file_hash(
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

    Returns: hash value

    """
    with path.open("rb") as file:
        return hashing_strategy(file, hashing_algorithm, progress_reporter)


def validate_file_against_expected_hash(
    expected_hash: str, target_file: pathlib.Path
) -> Optional[List[str]]:
    prog_bar_format = (
        "{desc}{percentage:3.0f}% |{bar}| Time Remaining: {remaining}"
    )
    progress_bar = ProgressBar(
        total=100.0, leave=False, bar_format=prog_bar_format
    )
    progress_bar.set_description("Calculating hash")
    hash_value = get_file_hash(
        path=target_file,
        hashing_algorithm=hashlib.md5,
        progress_reporter=lambda value,  # type: ignore[misc]
        prog_bar=progress_bar: prog_bar.set_progress(value),
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
        result = get_file_hash(
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
            pre_fix = f"({i+1}/{len(files)}) "
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


def read_checksum_file(file_path: pathlib.Path) -> str:
    with open(file_path.absolute(), "r") as f:
        return f.read().strip()


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
