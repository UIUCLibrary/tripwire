import io
from unittest.mock import Mock

import pytest

from uiucprescon import tripwire
import sample_data


class TestTSVManifest:
    def test_read_file_data(self):
        # Test the TSVManifest class with a sample TSV file
        test_file = io.StringIO(sample_data.SAMPLE_AUDIO_MANIFEST_TSV_DATA)
        manifest = tripwire.files.TSVManifest(test_file)
        assert len(manifest) == 2
        assert manifest[0].row_data == {
            "": None,
            " Duration (HH:MM:SS)": "0:30:12",
            "Access Filename\n(MPEG-3)": "3503082_series17_box33_folder1_tape1_A_acc",  # noqa: E501
            "Cassette\nNo. ": "1",
            "Cassette Title": "Interview with Lou Harrison",
            "Condition Notes": "overall good, some dust at capstan and pinch roller openings, pressure pad is thin",  # noqa: E501
            "Date Recorded (M/D/YYYY) ": "1/1/1978",
            "Format": "Compact Cassette",
            "Housing Title": "Interviews Vol. 1",
            "Inspection Date (M/D/YYYY)": "9/2/21",
            "Photograph Filenames\n(JPEG)": "3503082_series17_box33_folder1_label1 thru label29\n",  # noqa: E501
            "Preservation Filename\n(WAVE, 96kHz/24bit)": "3503082_series17_box33_folder1_tape1_A_pres",  # noqa: E501
            "Side\n(A/B)": "A",
            "Transfer Date (M/D/YYYY)": "5/31/24",
            "Transfer Notes ": "Intelligible",
            "Transferred \nBy": "Scene Savers",
            "Treatment Given": "None",
        }
        assert manifest[1].row_data == {
            "": None,
            " Duration (HH:MM:SS)": "0:29:13",
            "Access Filename\n(MPEG-3)": "3503082_series17_box33_folder1_tape1_B_acc",  # noqa: E501
            "Cassette\nNo. ": "1",
            "Cassette Title": "Interview with Lou Harrison",
            "Condition Notes": "overall good, some dust at capstan and pinch roller openings, pressure pad is thin",  # noqa: E501
            "Date Recorded (M/D/YYYY) ": "1/1/1978",
            "Format": "Compact Cassette",
            "Housing Title": "Interviews Vol. 1",
            "Inspection Date (M/D/YYYY)": "9/2/21",
            "Photograph Filenames\n(JPEG)": "",
            "Preservation Filename\n(WAVE, 96kHz/24bit)": "3503082_series17_box33_folder1_tape1_B_pres",  # noqa: E501
            "Side\n(A/B)": "B",
            "Transfer Date (M/D/YYYY)": "5/31/24",
            "Transfer Notes ": "Intelligible",
            "Transferred \nBy": "Scene Savers",
            "Treatment Given": "None",
        }

    def test_iter(self):
        test_file = io.StringIO(sample_data.SAMPLE_AUDIO_MANIFEST_TSV_DATA)
        manifest = tripwire.files.TSVManifest(test_file)
        rows = list(manifest)
        assert len(rows) == 2
        assert (
            rows[0].row_data["Cassette Title"] == "Interview with Lou Harrison"
        )

    def test_line_number(self):
        test_file = io.StringIO(sample_data.SAMPLE_AUDIO_MANIFEST_TSV_DATA)
        manifest = tripwire.files.TSVManifest(test_file)
        row = manifest[0]
        assert row.line_number == 9

    def test_get_single_item(self):
        test_file = io.StringIO(sample_data.SAMPLE_AUDIO_MANIFEST_TSV_DATA)
        manifest = tripwire.files.TSVManifest(test_file)
        row = manifest[0]
        assert row["Side\n(A/B)"] == "A"
        assert row.line_number == 9

    def test_get_slice(self):
        test_file = io.StringIO(sample_data.SAMPLE_AUDIO_MANIFEST_TSV_DATA)
        manifest = tripwire.files.TSVManifest(test_file)
        rows = manifest[0:2]
        assert len(rows) == 2
        assert rows[0]["Side\n(A/B)"] == "A"
        assert rows[1]["Side\n(A/B)"] == "B"

    @pytest.mark.parametrize("index", [2, slice(0, 3)])
    def test_out_of_bounds(self, index):
        test_file = io.StringIO(sample_data.SAMPLE_AUDIO_MANIFEST_TSV_DATA)
        manifest = tripwire.files.TSVManifest(test_file)
        with pytest.raises(IndexError):
            _ = manifest[index]

    def test_is_valid_file_call_TSVManifestReader(self, monkeypatch):
        test_file = io.StringIO("not\tvalid\tfile\n")
        is_valid_file = Mock(name="is_valid_file", return_value=True)
        monkeypatch.setattr(
            tripwire.files._TSVManifestReader, "is_valid_file", is_valid_file
        )
        manifest = tripwire.files.TSVManifest(test_file)
        assert manifest.is_valid_file() is True
        is_valid_file.assert_called_once_with(fp=test_file)


class TestInvalidFileFormat:
    def test_with_file_named(self):
        with pytest.raises(tripwire.files.InvalidFileFormat) as error:
            raise tripwire.files.InvalidFileFormat("my_file.xlsx")
        assert str(error.value) == "Invalid file format. File: my_file.xlsx"

    def test_without_file_named(self):
        with pytest.raises(tripwire.files.InvalidFileFormat) as error:
            raise tripwire.files.InvalidFileFormat
        assert str(error.value) == "Invalid file format"


class Test_TSVManifestReader:
    @pytest.fixture
    def validator_with_findings(self):
        def validator(findings):
            return Mock(
                name="validator that will always find wrong",
                spec_set=tripwire.files.AbsFileValidator,
                get_validation_findings=Mock(
                    name="get_validation_findings", return_value=findings
                ),
            )

        return validator

    @pytest.mark.parametrize(
        "findings, expected_valid",
        [
            ([], True),
            (
                [
                    tripwire.files.Finding(
                        tripwire.files.ValidationFindingLevel.ERROR,
                        message="one bad one",
                    )
                ],
                False,
            ),
            (
                [
                    tripwire.files.Finding(
                        tripwire.files.ValidationFindingLevel.WARNING,
                        message="Just a warning",
                    )
                ],
                True,
            ),
            (
                [
                    tripwire.files.Finding(
                        tripwire.files.ValidationFindingLevel.WARNING,
                        message="first warning",
                    ),
                    tripwire.files.Finding(
                        tripwire.files.ValidationFindingLevel.WARNING,
                        message="second warning",
                    ),
                ],
                True,
            ),
            (
                [
                    tripwire.files.Finding(
                        tripwire.files.ValidationFindingLevel.WARNING,
                        message="Just a warning",
                    ),
                    tripwire.files.Finding(
                        tripwire.files.ValidationFindingLevel.ERROR,
                        message="full error",
                    ),
                ],
                False,
            ),
        ],
    )
    def test_is_valid_file_finding(
        self, validator_with_findings, monkeypatch, findings, expected_valid
    ):
        test_file = io.StringIO("not\tvalid\tfile\n")
        with monkeypatch.context() as m:
            m.setattr(
                tripwire.files,
                "DEFAULT_FILE_VALIDATORS",
                {
                    tripwire.files.SupportedFileTypes.MANIFEST_TSV: Mock(
                        return_value=validator_with_findings(findings)
                    )
                },
            )
            assert (
                tripwire.files._TSVManifestReader.is_valid_file(fp=test_file)
                is expected_valid
            )

    @pytest.mark.parametrize(
        "finding, expected_log_level, expected_message",
        [
            (
                tripwire.files.Finding(
                    tripwire.files.ValidationFindingLevel.WARNING,
                    message="Just a warning",
                ),
                "WARNING",
                "Just a warning",
            ),
            (
                tripwire.files.Finding(
                    tripwire.files.ValidationFindingLevel.ERROR,
                    message="This one is an error",
                ),
                "ERROR",
                "This one is an error",
            ),
            (
                tripwire.files.Finding(
                    "something else",
                    message="some odd results",
                ),
                "WARNING",
                (
                    "Unknown validation level. level: something else. "
                    'message: "some odd results"'
                ),
            ),
        ],
    )
    def test_is_valid_file_logging(
        self,
        validator_with_findings,
        monkeypatch,
        caplog,
        finding,
        expected_log_level,
        expected_message,
    ):
        test_file = io.StringIO("not\tvalid\tfile\n")
        with monkeypatch.context() as m:
            m.setattr(
                tripwire.files,
                "DEFAULT_FILE_VALIDATORS",
                {
                    tripwire.files.SupportedFileTypes.MANIFEST_TSV: Mock(
                        return_value=validator_with_findings([finding])
                    )
                },
            )
            tripwire.files._TSVManifestReader.is_valid_file(fp=test_file)
        assert all(
            (
                record.levelname == expected_log_level
                and record.message == expected_message
            )
            for record in caplog.records
        ), (
            f'expected message = "{expected_message}", '
            f'actual message = "{" ".join([record.message for record in caplog.records])}", '  # noqa: E501
            f"expected level = {expected_log_level}, "
            f"actual level = {' '.join([record.levelname for record in caplog.records])}"  # noqa: E501
        )


def test_find_validator_factory(monkeypatch):
    validator = Mock(spec_set=tripwire.files.AbsFileValidator)
    validator_klass = Mock(
        spec_set=tripwire.files.AbsFileValidator, return_value=validator
    )
    fp = Mock(name="file handle")

    with monkeypatch.context() as m:
        m.setattr(
            tripwire.files,
            "DEFAULT_FILE_VALIDATORS",
            {tripwire.files.SupportedFileTypes.MANIFEST_TSV: validator_klass},
        )
        result = tripwire.files.find_validator_factory(
            fp, tripwire.files.SupportedFileTypes.MANIFEST_TSV
        )
        result.get_validation_findings()

    validator_klass.assert_called_once_with(fp)
    validator.get_validation_findings.assert_called_once_with()


def test_find_validator_factory_missing_throws_value_error(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(tripwire.files, "DEFAULT_FILE_VALIDATORS", {})
        with pytest.raises(ValueError):
            tripwire.files.find_validator_factory(
                Mock(name="file handle"),
                tripwire.files.SupportedFileTypes.MANIFEST_TSV,
            )


class TestManifestTSVAbsFileValidator:
    def test_override_validations(self):
        validator = tripwire.files.ManifestTSVAbsFileValidator(io.StringIO(""))
        validator.validations = []
        assert len(validator.get_validation_findings()) == 0

    @pytest.mark.parametrize(
        "data",
        [
            sample_data.SAMPLE_AUDIO_MANIFEST_TSV_DATA,
            sample_data.SAMPLE_VIDEO_MANIFEST_TSV_DATA,
        ],
    )
    def test_valid_file(self, data):
        test_file = io.StringIO(data)
        validator = tripwire.files.ManifestTSVAbsFileValidator(test_file)
        assert len(validator.get_validation_findings()) == 0

    def test_invalid_file(self):
        validator = tripwire.files.ManifestTSVAbsFileValidator(io.StringIO(""))
        validator.validations = [
            Mock(
                name="validation that will always find wrong",
                return_value=[
                    tripwire.files.Finding(
                        level=tripwire.files.ValidationFindingLevel.ERROR,
                        message="something",
                    )
                ],
            )
        ]
        assert len(validator.get_validation_findings()) == 1


@pytest.mark.parametrize(
    "data",
    [
        sample_data.SAMPLE_AUDIO_MANIFEST_TSV_DATA,
        sample_data.SAMPLE_VIDEO_MANIFEST_TSV_DATA,
    ],
)
def test_discover_manifest_tsv_findings(data):
    assert (
        len(tripwire.files.discover_manifest_tsv_findings(io.StringIO(data)))
        == 0
    )


def test_discover_manifest_tsv_findings_no_rows_has_warning():
    findings = tripwire.files.discover_manifest_tsv_findings(
        io.StringIO("not\tvalid\tfile\n")
    )
    assert len(findings) == 1
    assert list(findings)[0].message == "No rows in the file."


def test_discover_manifest_tsv_findings_bad_data():
    findings = tripwire.files.discover_manifest_tsv_findings(
        io.BytesIO(b"bad data")
    )
    assert len(findings) == 1
    assert (
        list(findings)[0].message
        == tripwire.files.INVALID_MANIFEST_TSV_ERROR_MESSAGE
    )
