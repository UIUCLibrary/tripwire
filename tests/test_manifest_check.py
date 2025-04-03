import io
import pathlib
from unittest.mock import Mock, MagicMock

import pytest

from uiucprescon.tripwire import manifest_check
from uiucprescon.tripwire.files import TSVManifest


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
    manifest_check.locate_manifest_files(
        manifest_tsv, search_path=pathlib.Path("test_path")
    )
    assert any(["some_file" in rec.message for rec in caplog.records])


@pytest.fixture
def sample_tsv_data():
    return """
Housing Title	"Cassette
No. "	"Side
(A/B)"	Cassette Title	Date Recorded (M/D/YYYY) 	Format	Condition Notes	Inspection Date (M/D/YYYY)	Treatment Given	"Preservation Filename
(WAVE, 96kHz/24bit)"	"Access Filename
(MPEG-3)"	"Photograph Filenames
(JPEG)"	 Duration (HH:MM:SS)	Transfer Notes 	Transfer Date (M/D/YYYY)	"Transferred 
By"										
Interviews Vol. 1	1	A	Interview with Lou Harrison	1/1/1978	Compact Cassette	"overall good, some dust at capstan and pinch roller openings, pressure pad is thin"	9/2/21	None	3503082_series17_box33_folder1_tape1_A_pres	3503082_series17_box33_folder1_tape1_A_acc	"3503082_series17_box33_folder1_label1 thru label29
"	0:30:12	Intelligible	5/31/24	Scene Savers
Interviews Vol. 1	1	B	Interview with Lou Harrison	1/1/1978	Compact Cassette	"overall good, some dust at capstan and pinch roller openings, pressure pad is thin"	9/2/21	None	3503082_series17_box33_folder1_tape1_B_pres	3503082_series17_box33_folder1_tape1_B_acc		0:29:13	Intelligible	5/31/24	Scene Savers
""".strip()


def test_locate_manifest_files_fp(monkeypatch, sample_tsv_data):
    manifest_tsv = io.StringIO(sample_tsv_data)
    search_path = Mock()
    monkeypatch.setattr(TSVManifest, "is_valid_file", lambda *_: True)
    get_items_check_to_locate = Mock(return_value=[])
    monkeypatch.setattr(
        manifest_check, "get_items_check_to_locate", get_items_check_to_locate
    )
    manifest_check.locate_manifest_files_fp(manifest_tsv, search_path)

    get_items_check_to_locate.assert_called()


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
