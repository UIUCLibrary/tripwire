import pathlib
from unittest.mock import Mock, MagicMock
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


def get_hash_from_file_pointer_progress():
    reporter = Mock()
    validation.get_hash_from_file_pointer(
        io.BytesIO(b"abcdef"), hashlib.md5, progress_reporter=reporter
    )
    assert reporter.mock_calls[-1].args[0] == 100


def test_get_file_hash(monkeypatch):
    hashing_strategy = Mock()
    file_path = Mock()
    file_path.open = MagicMock()
    validation.get_file_hash(
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
