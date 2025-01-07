import io
import pathlib
from typing import BinaryIO, Optional, Callable, Any


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
