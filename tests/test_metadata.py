import json
import logging
import os
import pathlib
import shutil
from unittest.mock import Mock, patch

import pytest
from pygments.lexers import wowtoc

from uiucprescon.tripwire import metadata as metadata_module
import sample_media_files

TRIPWIRE_SAMPLE_FILES_ENV_VARIABLE = "TRIPWIRE_SAMPLE_FILES"

@pytest.mark.parametrize(
    "terminal_width, expected", [(80, 80), (100, 100), (200, 160), (50, 80)]
)
def test_get_console_print_width(terminal_width, expected):
    assert metadata_module.get_console_print_width(terminal_width) == expected


def test_generate_metadata_report():
    file = "test_file.mp3"
    metadata = {
        "title": "Test Title",
        "artist": "Test Artist",
        "duration": 300,
    }
    report = metadata_module.generate_metadata_report(file, metadata)

    assert file in report
    assert "metadata:" in report
    assert "'title': 'Test Title'" in report
    assert "'duration': 300" in report


def test_get_media_metadata(monkeypatch):
    parse = Mock(spec_set=metadata_module.pymediainfo.MediaInfo.parse)
    monkeypatch.setattr(metadata_module.pymediainfo.MediaInfo, "parse", parse)
    metadata_module.get_media_metadata("test_file.mp3")
    parse.assert_called_with("test_file.mp3")


def test_show_metadata():
    glob = "*.mp3"
    find_files_strategy = Mock(return_value=["test_file.mp3"])
    get_file_metadata_strategy = Mock(
        return_value={"title": "Test Title", "artist": "Test Artist"}
    )

    metadata_module.show_metadata(
        glob=glob,
        find_files_strategy=find_files_strategy,
        get_file_metadata_strategy=get_file_metadata_strategy,
    )

    find_files_strategy.assert_called_once_with(glob)
    get_file_metadata_strategy.assert_called_with(
        pathlib.Path("test_file.mp3")
    )


def test_show_metadata_no_files(caplog):
    find_files_strategy = Mock(return_value=[])
    metadata_module.show_metadata(
        glob="*.mp3", find_files_strategy=find_files_strategy
    )
    assert "Found no files" in caplog.text


def test_locate_files(monkeypatch):
    mock_glob = Mock(return_value=["dummy.mp3"])
    monkeypatch.setattr(metadata_module.glob_module, "iglob", mock_glob)
    assert list(metadata_module.locate_files("*.mp3", filters=[])) == [
        "dummy.mp3"
    ]

@pytest.fixture(scope="session")
def sample_files(tmp_path_factory):
    if not any(condition for condition in [
        os.getenv(TRIPWIRE_SAMPLE_FILES_ENV_VARIABLE),
        shutil.which('ffmpeg')
    ]):
        pytest.skip(
            f"neither environment variable "
            f"{TRIPWIRE_SAMPLE_FILES_ENV_VARIABLE} nor ffmpeg was found, "
            f"skipping integration test"
        )
    if sample_file_path := os.getenv(TRIPWIRE_SAMPLE_FILES_ENV_VARIABLE):
        return sample_media_files.get_sample_files(sample_file_path)

    return sample_media_files.create_sample_files(tmp_path_factory.mktemp('samples'))

def test_locate_files_uses_default_filters(monkeypatch):
    mock_glob = Mock(return_value=["dummy.mp3"])
    monkeypatch.setattr(metadata_module.glob_module, "iglob", mock_glob)
    mock_filter = Mock(return_value=False)
    metadata_module.LOCATE_FILE_DEFAULT_FILTERS = [mock_filter]
    list(metadata_module.locate_files("*.mp3"))
    mock_filter.assert_called_once_with("dummy.mp3")


def test_get_terminal_width_falls_back():
    with patch(
        "uiucprescon.tripwire.metadata.shutil.get_terminal_size"
    ) as mock_get_terminal_size:
        mock_get_terminal_size.side_effect = OSError
        assert (
            metadata_module.get_terminal_width() == 80
        )  # Default fallback value


def test_get_terminal_width_uses_shutil(monkeypatch):
    with patch(
        "uiucprescon.tripwire.metadata.shutil.get_terminal_size"
    ) as mock_get_terminal_size:
        mock_get_terminal_size.return_value = Mock(columns=100)
        assert (
            metadata_module.get_terminal_width() == 100
        )  # Should return the mocked terminal width


@pytest.mark.parametrize("valid", [True, False])
def test_validate_metadata_validates_based_on_valid_results(valid):
    glob = "*.mov"
    validate_strategy = Mock(
        name="validation strategy",
        spec_set=metadata_module.AbsValidateStrategy,
        validate=(
            Mock(
                name="validate",
                return_value=Mock(
                    name="result", files_with_issues=[], valid=valid
                ),
            )
        ),
    )
    assert (
        metadata_module.validate_metadata(
            glob=glob,
            policy_xml_file=pathlib.Path("test_file.xml"),
            validate_strategy=validate_strategy,
        )
        is valid
    )


def test_validate_metadata_prints_issues(caplog):
    glob = "*.mov"
    file_issues = {
        metadata_module.FileIssues(
            file="dummy.mov", issues={"Issue 1", "Issue 2"}
        )
    }
    validate_strategy = Mock(
        name="validation strategy",
        spec_set=metadata_module.AbsValidateStrategy,
        validate=Mock(
            return_value=metadata_module.ValidationResult(
                valid=False, files_with_issues=file_issues
            )
        ),
    )
    metadata_module.validate_metadata(
        glob=glob,
        policy_xml_file=pathlib.Path("test_file.xml"),
        validate_strategy=validate_strategy,
    )
    for file_issue in file_issues:
        for issue in file_issue.issues:
            assert issue in caplog.text


class TestMediaConchValidator:
    @pytest.mark.parametrize(
        "json_data, expected_levelname",
        [
            (
                json.dumps({
                    "MediaConch": {
                        "media": [
                            {
                                "ref": "dummy.mov",
                                "policies": [
                                    {
                                        "outcome": "pass",
                                        "rules": [
                                            {
                                                "actual": "24",
                                                "name": "24 bit",
                                                "occurrence": "*",
                                                "operator": "=",
                                                "outcome": "pass",
                                                "requested": "24",
                                                "tracktype": "Audio",
                                                "value": "BitDepth",
                                                "xpath": "mi:MediaInfo/mi:track[@type='Audio'][*]/mi:BitDepth",
                                            },
                                        ],
                                    }
                                ],
                            }
                        ]
                    }
                }),
                "INFO",
            ),
            (
                json.dumps({
                    "MediaConch": {
                        "media": [
                            {
                                "ref": "dummy.mov",
                                "policies": [
                                    {
                                        "outcome": "fail",
                                        "rules": [
                                            {
                                                "actual": "25",
                                                "name": "24 bit",
                                                "occurrence": "*",
                                                "operator": "=",
                                                "outcome": "fail",
                                                "requested": "24",
                                                "tracktype": "Audio",
                                                "value": "BitDepth",
                                                "xpath": "mi:MediaInfo/mi:track[@type='Audio'][*]/mi:BitDepth",
                                            },
                                        ],
                                    }
                                ],
                            }
                        ]
                    }
                }),
                "ERROR",
            ),
            (
                json.dumps({
                    "MediaConch": {
                        "media": [
                            {
                                "ref": "dummy.mov",
                                "policies": [
                                    {
                                        "outcome": "pass",
                                    }
                                ],
                            }
                        ]
                    }
                }),
                "INFO",
            ),
        ],
    )
    def test_validate_loging_valid(
        self, json_data, expected_levelname, caplog
    ):
        validator = metadata_module.MediaConchValidator()
        validator.validate_policy_file = lambda _: True
        validator.set_policy_file(pathlib.Path("test_file.xml"))
        validator.iglob = lambda *_, **__: ["dummy.mov"]
        validator.mediaconch = Mock(
            name="mediaconch",
            get_report=Mock(name="get_report", return_value=json_data),
        )
        validator.validate("*.mov")
        assert "Validating dummy.mov" in str(caplog.records[0])
        assert caplog.records[1].levelname == expected_levelname

    def test_validate_without_policy_file_produces_warning(self):
        validator = metadata_module.MediaConchValidator()
        validator.iglob = lambda *_, **__: ["dummy.mov"]
        validator.get_mediaconch_results = Mock(name="get_mediaconch_results", return_value=validator._Results())
        with pytest.warns(UserWarning):
            validator.validate("*.mov")

    def test_validate_raises_with_invalid_policy_file(self):
        validator = metadata_module.MediaConchValidator()
        validator.validate_policy_file = lambda _: False
        validator.set_policy_file(pathlib.Path("test_file.xml"))
        validator.iglob = lambda *_, **__: ["dummy.mov"]
        with pytest.raises(
            ValueError, match="Policy file must be valid policy file."
        ):
            validator.validate("*.mov")

    def test_cancel_with_control_c(self, caplog):
        validator = metadata_module.MediaConchValidator()
        validator.validate_policy_file = lambda _: True
        validator.set_policy_file(pathlib.Path("test_file.xml"))
        validator.iglob = Mock(side_effect=KeyboardInterrupt)
        validator.validate("*.mov")
        assert "Validation interrupted by user" in caplog.text

    def test_get_mediaconch_results_json_error_logged(
        self, caplog, monkeypatch
    ):
        caplog.set_level(logging.DEBUG)
        validator = metadata_module.MediaConchValidator()
        metadata_module.logger.setLevel(logging.DEBUG)

        mc = Mock(get_report=Mock(name="get_report", return_value="somedata"))
        with pytest.raises(json.JSONDecodeError):
            monkeypatch.setattr(
                json,
                "load",
                Mock(
                    side_effect=json.JSONDecodeError(
                        "Expecting value", "somedata", 0
                    )
                ),
            )
            validator.get_mediaconch_results("somefile", mc)
        assert "Failed to parse MediaConch" in caplog.text

    def test_integration(self, sample_files, tmp_path):
        bars = sample_files["bars_and_tone_file"]
        test_path = tmp_path / "test"
        test_path.mkdir()
        shutil.copyfile(bars, test_path / "bars.mp4")
        validator = metadata_module.MediaConchValidator()
        a = validator.validate(f"{test_path}/*.mp4")
        assert a.valid



class TestValidationReportBuilder:
    def test_add_file_issues(self):
        builder = metadata_module.ValidationReportBuilder()
        file_name = "file1.mov"
        issue = 'Rule "24 bit" failed.  Expected: 25, Got: 24'
        builder.add_file_issue("file1.mov", issue)
        report = builder.build_report()
        assert all([file_name in report, issue in report]), (
            f"Report should contain file name and issue. Got:\n{report}"
        )

    def test_no_issues(self):
        builder = metadata_module.ValidationReportBuilder()
        report = builder.build_report()
        assert "No issues found." in report, (
            f"Report should indicate no issues. Got:\n{report}"
        )
