import pathlib
from unittest.mock import Mock, MagicMock
import pytest
speedwagon =  pytest.importorskip("speedwagon")
import speedwagon.tasks
from uiucprescon.tripwire.speedwagon_workflows import workflows as tripwire_workflows


class TestMediaConchValidateGlobString:
    @pytest.mark.parametrize("candidate, validation_response, expected", [
        ("/tmp/some/file.mov", True, []),
        ("..", False, ['".." is not a valid glob expression']),
        ("", False, ['"" is not a valid glob expression']),
        (None, False, ['"None" is not a valid glob expression']),
    ])
    def test_validate_glob_string(self, candidate,validation_response, expected, monkeypatch):
        validator = tripwire_workflows.MediaConchValidateGlobString()
        validator_strategy = Mock(return_value=validation_response)
        monkeypatch.setattr(tripwire_workflows.MediaConchValidateGlobString, "validator_strategy", validator_strategy)
        result = validator.investigate(candidate, {'Policy File': 'test.xml'})
        assert sorted(result) == sorted(expected)

    def test_validate_without_policy_file(self, monkeypatch):
        validator = tripwire_workflows.MediaConchValidateGlobString()
        validator_strategy = Mock(return_value=True)
        monkeypatch.setattr(tripwire_workflows.MediaConchValidateGlobString, "validator_strategy", validator_strategy)
        result = validator.investigate("/tmp/some/file.mov", {})
        assert result == ['Unable to validate without a policy file set in job options']

def test_valid_glob_with_mediaconch():
    mock_validator = Mock(name="MediaConchValidator", policy_file=None)
    tripwire_workflows.valid_glob_with_mediaconch(policy_file="test.xml", glob_expression="/tmp/some/*.mov", validator_strategy=Mock(return_value=mock_validator))
    mock_validator.validate.assert_called_once_with("/tmp/some/*.mov")


class TestIsMediaConchPoliceFile:
    def test_get_policy_file_issues(self):
        validator = tripwire_workflows.IsMediaConchPoliceFile()
        validator.get_policy_file_issues_strategy = Mock(return_value=[])
        file_path = MagicMock()
        validator.get_policy_file_issues(file_path)
        validator.get_policy_file_issues_strategy.assert_called_once()

    def test_investigate_uses_checks(self):
        validator = tripwire_workflows.IsMediaConchPoliceFile()
        mock_check = Mock(return_value=[])
        validator.checks = [mock_check]

        validator.investigate("/tmp/some/file.xml", {})
        mock_check.assert_called_once_with(pathlib.Path("/tmp/some/file.xml"))

    @pytest.mark.parametrize("candidate", ["", None])
    def test_investigate_with_empty_candidate(self, candidate):
        validator = tripwire_workflows.IsMediaConchPoliceFile()
        assert validator.investigate(candidate, {}) == [
            "Invalid policy file path"
        ]

class TestRedirectHandler:
    def test_emit(self):
        target_logger = Mock()
        handler = tripwire_workflows.RedirectHandler(target_logger)
        handler.emit("test")
        target_logger.handle.assert_called_once_with("test")

def test_hash_file_task_use_strategy():
    strategy = Mock(return_value="d41d8cd98f00b204e9800998ecf8427e")
    task = tripwire_workflows.hash_file_task("test.txt", "md5", strategy=strategy)
    task.work()
    strategy.assert_called_once_with("test.txt", "md5")

def test_hash_file_task_returns_hash():
    strategy = Mock(return_value="d41d8cd98f00b204e9800998ecf8427e")
    task = tripwire_workflows.hash_file_task("test.txt", "md5", strategy=strategy)
    task.work()
    assert task.task_result.data['hash'] == "d41d8cd98f00b204e9800998ecf8427e"

def test_get_hash_and_report():
    hash_strategy = Mock(return_value="d41d8cd98f00b204e9800998ecf8427e")
    tripwire_workflows.get_hash_and_report("test.txt", "md5", hash_strategy=hash_strategy)

@pytest.mark.parametrize(
    "workflow_klass",
    [
        tripwire_workflows.GetHashWorkflow,
        tripwire_workflows.ManifestCheckWorkflow,
        tripwire_workflows.MetadataValidateWorkflow,
        tripwire_workflows.MetadataShowWorkflow,
        tripwire_workflows.ValidateChecksumWorkflow,
    ]
)
def test_all_workflows_have_valid_job_options(workflow_klass):
    workflow = workflow_klass()
    assert workflow.job_options()


class TestGetHashWorkflow:
    def test_generate_report(self):
        results = [
            speedwagon.tasks.Result(
                source=Mock(),
                data={
                    "hash": "d41d8cd98f00b204e9800998ecf8427e",
                    "file": "test.txt"
                }
            )
        ]
        report = tripwire_workflows.GetHashWorkflow.generate_report(results, {"Hashing Algorithm": "md5"})
        assert all([
            "test.txt" in report,
            "d41d8cd98f00b204e9800998ecf8427e" in report
        ])

    def test_discover_task_metadata(self):
        workflow = tripwire_workflows.GetHashWorkflow()
        user_args = {"Hashing Algorithm": "md5"}
        results = workflow.discover_task_metadata(
            initial_results=[],
            additional_data={},
            user_args=user_args,
        )
        assert results == [user_args]

    def test_create_new_task(self):
        workflow = tripwire_workflows.GetHashWorkflow()
        job_args = {
            "Hashing Algorithm": "md5",
            "File": "something.txt",
        }
        task_builder = Mock()
        workflow.create_new_task(task_builder, job_args)
        task_builder.add_subtask.assert_called_once()

def test_validate_checksums_task_uses_strategy():
    file_path = "test.txt"
    validate_directory_strategy = Mock()
    task = tripwire_workflows.validate_checksums_task(file_path, validate_directory_strategy=validate_directory_strategy)
    task.work()
    validate_directory_strategy.assert_called_once()

def test_show_metadata_task_uses_strategy():
    file_path = "test.txt"
    get_metadata_strategy = Mock()
    task = tripwire_workflows.show_metadata_task(file_path, get_metadata_strategy=get_metadata_strategy)
    task.work()
    get_metadata_strategy.assert_called_once()

class TestMetadataShowWorkflow:
    def test_generate_report(self):
        results = [
            speedwagon.tasks.Result(
                source=Mock(),
                data={
                    "file": "test.txt",
                    "result": {"title": "Test File"}
                }
            )
        ]
        user_args = {"glob": "test.txt"}
        report = tripwire_workflows.MetadataShowWorkflow.generate_report(results, user_args)
        assert "test.txt" in report

    def test_create_new_task(self):
        workflow = tripwire_workflows.MetadataShowWorkflow()
        task_builder = Mock()
        job_args = {"file": "test.txt"}
        workflow.create_new_task(task_builder,job_args)
        task_builder.add_subtask.assert_called_once()

    def test_create_new_task_with_no_file(self):
        workflow = tripwire_workflows.MetadataShowWorkflow()
        task_builder = Mock()
        job_args = {}
        workflow.create_new_task(task_builder,job_args)
        task_builder.add_subtask.assert_not_called()

    def test_discover_task_metadata(self):
        workflow = tripwire_workflows.MetadataShowWorkflow()
        workflow.locate_files_strategy = Mock(return_value=["test.txt"])
        user_args = {"glob": "*.txt"}
        results = workflow.discover_task_metadata(
            initial_results=[],
            additional_data={},
            user_args=user_args,
        )
        assert results == [{"file": "test.txt"}]


    def test_discover_task_metadata_no_files_produces_warning(self, caplog):
        workflow = tripwire_workflows.MetadataShowWorkflow()
        workflow.locate_files_strategy = Mock(return_value=[])
        user_args = {"glob": "*.txt"}
        results = workflow.discover_task_metadata(
            initial_results=[],
            additional_data={},
            user_args=user_args,
        )
        assert results == []
        assert any(
            record.getMessage() == "No files found matching the glob pattern."
            for record in caplog.records if record.levelname == "WARNING"
        )

class TestMetadataValidateWorkflow:
    def test_discover_task_metadata(self):
        users_args = {
            'Policy File': 'some_policy.xml',
            "glob": "*.txt"
        }
        workflow = tripwire_workflows.MetadataValidateWorkflow()
        metadata = workflow.discover_task_metadata(
            initial_results=[],
            additional_data={},
            user_args=users_args,
        )
        assert metadata == [
            {
                "policy_file": "some_policy.xml",
                "glob": "*.txt"
            },
        ]

    def test_create_new_task(self):
        workflow = tripwire_workflows.MetadataValidateWorkflow()
        builder = Mock()
        job_args = {
            "policy_file": "some_policy.xml",
            "glob": "*.txt"
        }
        workflow.create_new_task(builder, job_args)
        builder.add_subtask.assert_called_once()

def test_validate_metadata_task_uses_strategy():
    validate_metadata_strategy = Mock()
    task = tripwire_workflows.validate_metadata_task("some_policy.xml", "*.txt", validate_metadata_strategy)
    task.work()
    validate_metadata_strategy.assert_called_once_with("*.txt", pathlib.Path("some_policy.xml"))

class TestValidateChecksumWorkflow:
    def test_discover_task_metadata(self):
        workflow = tripwire_workflows.ValidateChecksumWorkflow()
        user_args = {
            "path": "/path/to/files"
        }
        metadata = workflow.discover_task_metadata(
            initial_results=[],
            additional_data={},
            user_args=user_args,
        )
        assert metadata == [
            {
                "path": "/path/to/files"
            }
        ]

    def test_create_new_task(self):
        workflow = tripwire_workflows.ValidateChecksumWorkflow()
        task_builder = Mock()
        job_args = {
            "path": "/path/to/files"
        }
        workflow.create_new_task(task_builder,job_args)
        task_builder.add_subtask.assert_called_once()
