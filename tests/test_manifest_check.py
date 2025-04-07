import io
import pathlib
from unittest.mock import Mock, MagicMock

import pytest

from uiucprescon.tripwire import manifest_check
from uiucprescon.tripwire.files import TSVManifest, InvalidFileFormat
import sample_data


def test_locate_manifest_files_logs_extra_files(monkeypatch, caplog):
    manifest_tsv = Mock(open=MagicMock())
    monkeypatch.setattr(
        manifest_check,
        "locate_manifest_files_fp",
        Mock(
            name="locate_manifest_files_fp",
            return_value=[Mock(name="some_file")],
        ),
    )
    monkeypatch.setattr(manifest_check, "get_manifest_type", Mock())
    manifest_check.locate_manifest_files(
        manifest_tsv, search_path=pathlib.Path("test_path")
    )
    assert any(["some_file" in rec.message for rec in caplog.records])


def test_locate_manifest_files_invalid_file_format(monkeypatch):
    manifest_tsv = Mock(open=MagicMock())
    monkeypatch.setattr(
        manifest_check,
        "locate_manifest_files_fp",
        Mock(
            name="locate_manifest_files_fp",
            side_effect=InvalidFileFormat("Invalid file format"),
        ),
    )
    monkeypatch.setattr(manifest_check, "get_manifest_type", Mock())
    with pytest.raises(InvalidFileFormat):
        manifest_check.locate_manifest_files(
            manifest_tsv, search_path=pathlib.Path("test_path")
        )


@pytest.mark.parametrize(
    "data",
    [
        sample_data.SAMPLE_AUDIO_MANIFEST_TSV_DATA,
        sample_data.SAMPLE_VIDEO_MANIFEST_TSV_DATA,
        sample_data.SAMPLE_FILM_MANIFEST_TSV_DATA,
    ],
)
def test_locate_manifest_files_fp(monkeypatch, data):
    manifest_tsv = io.StringIO(data)
    search_path = Mock()
    monkeypatch.setattr(TSVManifest, "is_valid_file", lambda *_: True)
    locate_missing_files = Mock(return_value=[])
    monkeypatch.setattr(
        manifest_check, "locate_missing_files", locate_missing_files
    )
    row_parser = manifest_check.get_manifest_type(fp=manifest_tsv)
    manifest_check.locate_manifest_files_fp(
        manifest_tsv, search_path, row_parser
    )

    locate_missing_files.assert_called()


def test_locate_manifest_files_fp_with_invalid_file(monkeypatch):
    manifest_tsv = io.StringIO("invalid data")
    search_path = Mock()
    monkeypatch.setattr(TSVManifest, "is_valid_file", lambda *_: False)
    locate_missing_files = Mock(return_value=[])
    monkeypatch.setattr(
        manifest_check, "locate_missing_files", locate_missing_files
    )
    with pytest.raises(InvalidFileFormat):
        manifest_check.locate_manifest_files_fp(
            manifest_tsv, search_path, Mock()
        )


def test_locate_missing_files():
    search_package = manifest_check.SearchPackage(
        preservation_file="somepresfile.wav",
        access_file="someaccesfile.wav",
    )
    scanner = Mock(
        spec_set=manifest_check.PackageScanner,
        locate=lambda file_name: "someaccesfile.wav"
        if file_name == "someaccesfile.wav"
        else None,
    )
    assert manifest_check.locate_missing_files(search_package, scanner) == {
        "preservation_file": "somepresfile.wav"
    }


class TestRecursiveFileSearch:
    def test_search(self):
        root = pathlib.Path("somepath")
        manifest_check.RecursiveFileSearch.walk = Mock(
            return_value=[("somepath", [], ["file1"])]
        )
        search = manifest_check.RecursiveFileSearch(root_path=root)

        assert list(search) == [pathlib.Path("somepath") / "file1"]


class TestPackageScanner:
    def test_file_not_located_is_none(self):
        root = pathlib.Path("somepath")
        scanner = manifest_check.PackageScanner(search_path=root)
        assert scanner.locate("some file") is None

    def test_file_located(self):
        root = pathlib.Path("somepath")
        mock_scanner = MagicMock(
            name="Scanner",
        )
        a = Mock()
        a.name = "some file"
        mock_scanner.__next__.side_effect = [a, StopIteration]
        manifest_check.PackageScanner.scanner_klass = Mock(
            return_value=mock_scanner
        )
        scanner = manifest_check.PackageScanner(search_path=root)
        assert scanner.locate("some file") is not None

    def test_locate_uses_cache(self):
        root = pathlib.Path("somepath")
        scanner = manifest_check.PackageScanner(search_path=root)
        d = {
            "some file.txt": manifest_check.PackageScanner.Cache(
                file_name="some file.txt",
                location=pathlib.Path("somepath") / "some location",
            )
        }
        scanner.cache = MagicMock()
        scanner.cache.__getitem__.side_effect = d.__getitem__
        scanner.cache.__contains__.side_effect = d.__contains__
        scanner.locate("some file.txt")
        scanner.cache.__getitem__.assert_called_with("some file.txt")

    def test_unexpected_files(self):
        root = pathlib.Path("somepath")
        scanner = manifest_check.PackageScanner(search_path=root)
        d = {
            "some file.txt": manifest_check.PackageScanner.Cache(
                file_name="some file.txt",
                location=pathlib.Path("somepath") / "some location",
                expected=False,
            )
        }
        scanner.cache = MagicMock()
        scanner.cache.__getitem__.side_effect = d.__getitem__
        scanner.cache.__contains__.side_effect = d.__contains__
        scanner.cache.items = d.items
        assert "some file.txt" not in scanner.unexpected_files()


class TestAbsManifestClasses:
    @pytest.mark.parametrize(
        "data, klass, expected",
        [
            (
                sample_data.SAMPLE_AUDIO_MANIFEST_TSV_DATA,
                manifest_check.AudioManifest,
                True,
            ),
            (
                sample_data.SAMPLE_VIDEO_MANIFEST_TSV_DATA,
                manifest_check.AudioManifest,
                False,
            ),
            (
                sample_data.SAMPLE_FILM_MANIFEST_TSV_DATA,
                manifest_check.AudioManifest,
                False,
            ),
            (
                sample_data.SAMPLE_AUDIO_MANIFEST_TSV_DATA,
                manifest_check.VideoManifest,
                False,
            ),
            (
                sample_data.SAMPLE_VIDEO_MANIFEST_TSV_DATA,
                manifest_check.VideoManifest,
                True,
            ),
            (
                sample_data.SAMPLE_FILM_MANIFEST_TSV_DATA,
                manifest_check.VideoManifest,
                False,
            ),
            (
                sample_data.SAMPLE_FILM_MANIFEST_TSV_DATA,
                manifest_check.FilmManifest,
                True,
            ),
            (
                sample_data.SAMPLE_AUDIO_MANIFEST_TSV_DATA,
                manifest_check.FilmManifest,
                False,
            ),
            (
                sample_data.SAMPLE_VIDEO_MANIFEST_TSV_DATA,
                manifest_check.FilmManifest,
                False,
            ),
        ],
    )
    def test_verify_format_type(self, data, klass, expected):
        manifest = klass()
        assert manifest.verify_format_type(io.StringIO(data)) is expected

    def test_get_manifest_type_unknown_throws(self):
        with pytest.raises(ValueError):
            manifest_check.get_manifest_type(io.StringIO("unknown format"))
