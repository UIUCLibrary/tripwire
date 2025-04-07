"""Manifest file checking."""

import abc
import os
import pathlib
import typing
from typing import Mapping, Set, MutableMapping, TextIO, Sequence, Type
import logging
from uiucprescon.tripwire import files as tripwire_files
from tqdm import tqdm

__all__ = ["locate_manifest_files"]

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SearchPackage(typing.TypedDict, total=False):
    preservation_file: str
    preservation_file_checksum: str
    access_file: str
    access_file_checksum: str
    photo_file: str
    photo_file_checksum: str


class AbsManifest(abc.ABC):
    """Abstract class for manifest."""

    @abc.abstractmethod
    def verify_format_type(self, fp: TextIO) -> bool:
        """Check if the file is the expect format."""

    @abc.abstractmethod
    def extract_files_from_manifest(
        self, row: Mapping[str, str]
    ) -> SearchPackage:
        """identify the files from a given row in the manifest."""


class FilmManifest(AbsManifest):
    """Film manifest."""

    def verify_format_type(self, fp: TextIO) -> bool:
        result = self.is_it_a_film_manifest(fp=fp)
        if result is True:
            logger.debug("Determined manifest type is a film manifest.")
        return result

    @staticmethod
    @tripwire_files.remembered_file_pointer
    def is_it_a_film_manifest(fp: TextIO) -> bool:
        try:
            manifest = tripwire_files.TSVManifest(fp)
            return "Date of Film (M/D/YYYY)" in manifest[0].row_data
        except IndexError:
            return False

    def extract_files_from_manifest(
        self, row: Mapping[str, str]
    ) -> SearchPackage:
        data: SearchPackage = {}
        preservation_key = "Preservation File Name\n(uncompressed, MOV)"
        if preservation_key in row and row[preservation_key]:
            data["preservation_file"] = f"{row[preservation_key]}.mov"
            data["preservation_file_checksum"] = (
                f"{row[preservation_key]}.mov.md5"
            )
        access_key = "Access File Name\n(MPEG-4)"
        if access_key in row and row[access_key]:
            data["access_file"] = f"{row[access_key]}.mp4"
            data["access_file_checksum"] = f"{row[access_key]}.mp4.md5"
        photo_key = "Photograph File Name\n(JPEG)"
        if photo_key in row and row[photo_key]:
            data["photo_file"] = f"{row[photo_key].strip()}.jpg"
            data["photo_file_checksum"] = f"{row[photo_key].strip()}.jpg.md5"
        return data


class VideoManifest(AbsManifest):
    """Video manifest."""

    @staticmethod
    @tripwire_files.remembered_file_pointer
    def is_it_a_video_manifest(fp: TextIO) -> bool:
        try:
            manifest = tripwire_files.TSVManifest(fp)
            has_cassette_no_key = "Cassette \nNo." in manifest[0].row_data
        except IndexError:
            return False
        if not has_cassette_no_key:
            return False
        if (
            """Side
(A/B)"""
            in manifest[0].row_data
        ):
            return False
        return True

    def verify_format_type(self, fp: TextIO) -> bool:
        result = self.is_it_a_video_manifest(fp=fp)
        if result:
            logger.debug("Determined manifest type is a video manifest.")
        return result

    def extract_files_from_manifest(
        self, row: Mapping[str, str]
    ) -> SearchPackage:
        data: SearchPackage = {}
        preservation_key = "Preservation File Name"
        if preservation_key in row and row[preservation_key]:
            data["preservation_file"] = f"{row[preservation_key]}.mov"
            data["preservation_file_checksum"] = (
                f"{row[preservation_key]}.mov.md5"
            )
        access_key = "Access File Name"
        if access_key in row and row[access_key]:
            data["access_file"] = f"{row[access_key]}.mp4"
            data["access_file_checksum"] = f"{row[access_key]}.mp4.md5"
        photo_key = "Photograph File Name"
        if photo_key in row and row[photo_key]:
            data["photo_file"] = f"{row[photo_key].strip()}.jpg"
            data["photo_file_checksum"] = f"{row[photo_key].strip()}.jpg.md5"
        return data


class AudioManifest(AbsManifest):
    """Audio manifest."""

    @staticmethod
    @tripwire_files.remembered_file_pointer
    def is_it_an_audio_manifest(fp: TextIO) -> bool:
        try:
            manifest = tripwire_files.TSVManifest(fp)
            return "Cassette Title" in manifest[0].row_data
        except IndexError:
            return False

    def verify_format_type(self, fp: TextIO) -> bool:
        result = self.is_it_an_audio_manifest(fp=fp)
        if result:
            logger.debug("Determined manifest type is an audio manifest.")
        return result

    def extract_files_from_manifest(
        self, row: Mapping[str, str]
    ) -> SearchPackage:
        data: SearchPackage = {}
        preservation_key = "Preservation Filename\n(WAVE, 96kHz/24bit)"
        if preservation_key in row and row[preservation_key]:
            data["preservation_file"] = f"{row[preservation_key]}.wav"
            data["preservation_file_checksum"] = (
                f"{row[preservation_key]}.wav.md5"
            )
        access_key = "Access Filename\n(MPEG-3)"
        if access_key in row and row[access_key]:
            data["access_file"] = f"{row[access_key]}.mp3"
            data["access_file_checksum"] = f"{row[access_key]}.mp3.md5"
        photo_key = "Photograph Filenames\n(JPEG)"
        if photo_key in row and row[photo_key]:
            data["photo_file"] = f"{row[photo_key].strip()}.jpg"
            data["photo_file_checksum"] = f"{row[photo_key].strip()}.jpg.md5"
        return data


# The order to determine the type of manifest file that a file
# handle points to. Used by get_manifest_type()

LOOK_UP_MANIFEST_CHECKS_ORDER: Sequence[Type[AbsManifest]] = [
    FilmManifest,
    VideoManifest,
    AudioManifest,
]


def get_manifest_type(fp: typing.TextIO) -> AbsManifest:
    for klass in LOOK_UP_MANIFEST_CHECKS_ORDER:
        manifest_type = klass()
        if manifest_type.verify_format_type(fp=fp):
            return manifest_type

    raise ValueError("unable to determine type of manifest")


class RecursiveFileSearch:
    walk = os.walk

    def __init__(self, root_path: pathlib.Path) -> None:
        self.root_path = root_path
        self.files_generator = self._recursive_search(self.root_path)

    @classmethod
    def _recursive_search(
        cls, path: pathlib.Path
    ) -> typing.Iterator[pathlib.Path]:
        for root, dirs, files_ in cls.walk(path):
            for file in files_:
                yield pathlib.Path(os.path.join(root, file))

    def __iter__(self) -> "RecursiveFileSearch":
        return self

    def __next__(self) -> pathlib.Path:
        return next(self.files_generator)


class PackageScanner:
    scanner_klass = RecursiveFileSearch

    class Cache(typing.TypedDict):
        file_name: str
        location: pathlib.Path
        expected: bool

    def __init__(self, search_path: pathlib.Path):
        self.search_path = search_path
        self.cache: typing.Dict[str, PackageScanner.Cache] = {}
        self._scanner = PackageScanner.scanner_klass(self.search_path)

    def locate(self, file_name: str) -> typing.Optional[pathlib.Path]:
        if file_name in self.cache:
            self.cache[file_name]["expected"] = True
            return self.cache[file_name]["location"] / file_name

        while True:
            try:
                entry = next(self._scanner)
                entry_file_name = entry.name
                self.cache[entry_file_name] = {
                    "file_name": entry_file_name,
                    "location": entry.parent,
                    "expected": entry_file_name == file_name,
                }
                if entry_file_name == file_name:
                    return entry
            except StopIteration:
                return None

    def unexpected_files(self) -> Set[pathlib.Path]:
        unexpected_files = set()
        for k, v in self.cache.items():
            if not v["expected"]:
                unexpected_files.add(v["location"] / v["file_name"])
        return unexpected_files


def locate_missing_files(
    package: SearchPackage, scanner: PackageScanner
) -> SearchPackage:
    results = typing.cast(MutableMapping[str, str], package.copy())
    if package:
        for k, v in package.items():
            if scanner.locate(typing.cast(str, v)) is not None:
                del results[k]
    return typing.cast(SearchPackage, results)


def locate_manifest_files_fp(
    manifest_tsv_fp: typing.TextIO,
    search_path: pathlib.Path,
    manifest_type: AbsManifest,
) -> Set[pathlib.Path]:
    prog_bar_format = (
        "{desc}{percentage:3.0f}% |{bar}| Time Remaining: {remaining}"
    )
    manifest = tripwire_files.TSVManifest(manifest_tsv_fp)
    if not manifest.is_valid_file():
        raise tripwire_files.InvalidFileFormat(
            details="Not a valid TSV manifest file."
        )

    scanner = PackageScanner(search_path)
    for row in (
        prog_bar := tqdm(manifest, bar_format=prog_bar_format, leave=False)
    ):
        if items_check := manifest_type.extract_files_from_manifest(
            row.row_data
        ):
            if missing_files := locate_missing_files(items_check, scanner):
                for k, v in missing_files.items():
                    prog_bar.write(
                        f"Line: {row.line_number}. Unable to locate: {v}"
                    )

    return scanner.unexpected_files()


def locate_manifest_files(
    manifest_tsv: pathlib.Path, search_path: pathlib.Path
) -> None:
    """Locate files listed in manifest in the search path.

    Args:
        manifest_tsv: manifest tsv file.
        search_path: Path to search recursively.
    """
    logger.debug(
        "manifest_check_command using %s and searching at %s",
        manifest_tsv,
        search_path,
    )
    try:
        with manifest_tsv.open("r", newline="", encoding="utf-8") as fp:
            manifest_type = get_manifest_type(fp=fp)
            unexpected_files = locate_manifest_files_fp(
                fp, search_path, manifest_type=manifest_type
            )
    except tripwire_files.InvalidFileFormat as e:
        raise tripwire_files.InvalidFileFormat(
            file=manifest_tsv.name, details=e.details
        ) from e
    if unexpected_files:
        list_of_unexpected_files = [
            f"* {f.relative_to(search_path)}" for f in sorted(unexpected_files)
        ]
        print()
        logger.info(
            "Files found that were not included in manifest: \n%s",
            "\n".join(list_of_unexpected_files),
        )
