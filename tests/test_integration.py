import argparse
import os
from unittest import mock

import pytest
import shutil
import sample_media_files

from uiucprescon.tripwire import main

SAMPLE_FILES_ENV_VARIABLE = 'TRIPWIRE_SAMPLE_FILES'

@pytest.fixture(scope="session")
def sample_files(tmp_path_factory):
    if not any(condition for condition in [
        os.getenv(SAMPLE_FILES_ENV_VARIABLE),
        shutil.which('ffmpeg')
    ]):
        pytest.skip(
            f"neither environment variable "
            f"{SAMPLE_FILES_ENV_VARIABLE} nor ffmpeg was found, "
            f"skipping integration test"
        )
    if sample_file_path := os.getenv(SAMPLE_FILES_ENV_VARIABLE):
        return sample_media_files.get_sample_files(sample_file_path)

    return sample_media_files.create_sample_files(tmp_path_factory.mktemp('samples'))

def test_integration_metadata_validate_command(sample_files, tmpdir, monkeypatch, caplog):
    test_path = tmpdir.mkdir('testing_area')

    policy_file = test_path / 'policy_file.xml'
    policy_file.write_text("""
<policy name="Root">
</policy>
        """.strip(),
        encoding="utf-8"
    )
    sample_files_path = test_path.mkdir('samples')
    bar_and_tone = sample_files_path / 'bars.mp4'
    shutil.copy(str(sample_files['bars_and_tone_file']), str(bar_and_tone))
    glob= test_path / '**/*.mp4'
    monkeypatch.chdir(test_path)
    cmd = argparse.Namespace(glob=f"{glob}", policy_file=policy_file, verbosity=1)
    mocked_exit = mock.Mock()
    monkeypatch.setattr(main.sys, "exit", mocked_exit)
    main.metadata_validate_command(cmd)
    assert "No issues found." in caplog.text and "Inspected 1 files" in caplog.text
