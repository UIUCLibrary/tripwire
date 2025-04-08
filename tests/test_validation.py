import pathlib
from unittest.mock import Mock, MagicMock, ANY
from uiucprescon.tripwire import validation
import hashlib
import io
import pytest


@pytest.mark.parametrize(
    "hashing_algorithm,expected",
    [
        (hashlib.md5, "e80b5017098950fc58aad83c8c14978e"),
        (hashlib.sha1, "1f8ac10f23c5b5bc1167bda84b833e5c057a77d2"),
    ],
)
def test_get_hash_from_file_pointer(hashing_algorithm, expected):
    assert (
        validation.get_hash_from_file_pointer(
            io.BytesIO(b"abcdef"), hashing_algorithm=hashing_algorithm
        )
        == expected
    )


def test_get_hash_from_file_pointer_progress():
    reporter = Mock()
    validation.get_hash_from_file_pointer(
        io.BytesIO(b"abcdef"), hashlib.md5, progress_reporter=reporter
    )
    assert reporter.mock_calls[-1].args[0] == 100


def test_get_file_hash(monkeypatch):
    hashing_strategy = Mock()
    file_path = Mock()
    file_path.open = MagicMock()
    validation.get_file_hash_with_progress_reporting(
        file_path,
        hashing_algorithm=hashlib.md5,
        hashing_strategy=hashing_strategy,
    )
    assert hashing_strategy.called


def test_validate_directory_checksums_command():
    compare_checksum_to_target_strategy = Mock(return_value=None)
    validation.validate_directory_checksums_command(
        path=pathlib.Path("dummy"),
        locate_checksum_strategy=lambda _: [
            (pathlib.Path("dummy") / "dummy.mp3.md5")
        ],
        read_checksums_strategy=lambda _: "123344",
        compare_checksum_to_target_strategy=compare_checksum_to_target_strategy,
    )
    compare_checksum_to_target_strategy.assert_called_once_with(
        "123344", (pathlib.Path("dummy") / "dummy.mp3")
    )


def test_locate_checksum_files(monkeypatch):
    path = pathlib.Path("dummy")
    file_path = path / "dummy.mp3"
    hash_file_path = path / "dummy.mp3.md5"
    monkeypatch.setattr(validation.os, "walk", lambda _: [(path, [], [file_path.name, hash_file_path.name])])
    assert list(validation.locate_checksum_files(path)) == [hash_file_path]

def test_validate_file_against_expected_hash():
    file_path = pathlib.Path("dummy.mp3")
    expected_hash = "e80b5017098950fc58aad83c8c14978e"
    get_file_hash_strategy = Mock(return_value=expected_hash)
    result = validation.validate_file_against_expected_hash(
        expected_hash, file_path, get_file_hash_strategy
    )
    assert result is None  # No errors

def test_validate_file_against_expected_hash_invalid():
    file_path = pathlib.Path("dummy.mp3")
    expected_hash = "e80b5017098950fc58aad83c8c14978e"
    get_file_hash_strategy = Mock(return_value="something else")
    result = validation.validate_file_against_expected_hash(
        expected_hash, file_path, get_file_hash_strategy
    )
    assert "Hash mismatch." in result[0]

def test_read_checksum_file():
    file_path = Mock(spec_set=pathlib.Path)
    file_path.open = MagicMock(
        side_effect=lambda mode: io.StringIO("e80b5017098950fc58aad83c8c14978e")
    )
    assert validation.read_checksum_file(file_path) == "e80b5017098950fc58aad83c8c14978e"

def test_get_hash_command(monkeypatch):
    files = [
        pathlib.Path("dummy.mp3")
    ]
    hashing_algorithm = "md5"
    get_file_hash_with_progress_reporting = Mock(return_value=lambda *args, **kwargs: None)
    monkeypatch.setattr(
        validation,
        "get_file_hash_with_progress_reporting",
        get_file_hash_with_progress_reporting
    )
    validation.get_hash_command(files, hashing_algorithm=hashing_algorithm)
    get_file_hash_with_progress_reporting.assert_called_once_with(
        files[0], hashing_algorithm=hashlib.md5, progress_reporter=ANY
    )
def test_create_checksum_validation_report():
    checksum_files_checked = [pathlib.Path("dummy.mp3")]
    errors = ["File not found"]
    report = validation.create_checksum_validation_report(
        checksum_files_checked, errors
    )
    assert "The following files failed:" in report
    assert "File not found" in report

def test_create_checksum_validation_report_no_errors():
    checksum_files_checked = [pathlib.Path("dummy.mp3")]
    errors = []
    report = validation.create_checksum_validation_report(
        checksum_files_checked, errors
    )
    assert "All 1 checksum(s) matched." in report

@pytest.mark.parametrize(
    "comparison_results, expected_message_in_log",
    [
        (["issue with dummy.mp3.md5"],"Failed"),
        ([],"Checksum matched"),
    ]
)
def test_validate_directory_checksums_command_failed(caplog, comparison_results, expected_message_in_log):
    path = pathlib.Path("dummy")
    locate_checksum_strategy = Mock(return_value=[path / "dummy.mp3.md5"])
    read_checksums_strategy = Mock(return_value="123344")
    compare_checksum_to_target_strategy = Mock(return_value=comparison_results)

    validation.validate_directory_checksums_command(
        path=path,
        locate_checksum_strategy=locate_checksum_strategy,
        read_checksums_strategy=read_checksums_strategy,
        compare_checksum_to_target_strategy=compare_checksum_to_target_strategy,
    )

    assert locate_checksum_strategy.called
    assert read_checksums_strategy.called
    assert compare_checksum_to_target_strategy.called
    assert expected_message_in_log in caplog.text