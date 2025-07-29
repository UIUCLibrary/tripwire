"""UIUC Preservation and Conservation Tripwire Metadata Module.

Added in version 0.3.3
"""

from __future__ import annotations

import io
import logging
import shutil
import glob as glob_module
import pprint
from typing import Dict, Union, Callable, Iterable, Optional, List
import pathlib
import pymediainfo

__all__ = ["show_metadata"]

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
