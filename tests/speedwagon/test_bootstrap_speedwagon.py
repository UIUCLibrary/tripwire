import logging
from unittest.mock import Mock
import pytest

speedwagon = pytest.importorskip("speedwagon")

from uiucprescon.tripwire.gui import bootstrap_speedwagon

@pytest.mark.parametrize("tab_file_exists, expected_to_create", [(True, False), (False, True)])
def test_set_tabs(monkeypatch, tab_file_exists, expected_to_create):
    config_file_location = {
        'app_data_directory': '/somewhere/.config/tripwire-speedwagon',
        'user_data_directory': '/somewhere/.config/tripwire-speedwagon/data',
        'tab_config_file': '/somewhere/tabs.yml'
    }
    write_tabs_strategy = Mock()
    monkeypatch.setattr(bootstrap_speedwagon.os.path, "exists", lambda x: tab_file_exists)
    bootstrap_speedwagon.set_tabs(config_file_location, write_tabs_strategy)
    assert write_tabs_strategy.called is expected_to_create

@pytest.mark.parametrize("config_file_exists, expected_to_create", [(True, False), (False, True)])
def test_verify_plugin_start_create_directory(monkeypatch, config_file_exists, expected_to_create):
    mock_write_config_strategy = Mock()
    exists = Mock(return_value=config_file_exists)
    mkdirs = Mock()
    monkeypatch.setattr(bootstrap_speedwagon.os.path, "exists",exists)
    monkeypatch.setattr(bootstrap_speedwagon.os, "makedirs", mkdirs)
    bootstrap_speedwagon.verify_plugin_start("/somewhere/config.ini", mock_write_config_strategy)
    assert mkdirs.called is expected_to_create

@pytest.mark.parametrize("config_file_exists, expected_to_create", [(True, False), (False, True)])
def test_verify_plugin_start_create_config_file(monkeypatch, config_file_exists, expected_to_create):
    mock_write_config_strategy = Mock()
    exists = Mock(return_value=config_file_exists)
    mkdirs = Mock()
    monkeypatch.setattr(bootstrap_speedwagon.os.path, "exists",exists)
    monkeypatch.setattr(bootstrap_speedwagon.os, "makedirs", mkdirs)
    bootstrap_speedwagon.verify_plugin_start("/somewhere/config.ini", mock_write_config_strategy)
    assert mock_write_config_strategy.called is expected_to_create

def test_get_arg_parser():
    parser = bootstrap_speedwagon.get_arg_parser()
    args = parser.parse_args(["run"])
    assert args.command == "run"


@pytest.mark.parametrize("args, expected_log_level", [
    (["--verbose"], logging.DEBUG),
    ([], logging.INFO)
])
def test_setup_bootstrap_logger(args, expected_log_level):
    bootstrap_speedwagon.setup_bootstrap_logger(args)
    assert bootstrap_speedwagon.bootstrap_logger.getEffectiveLevel() == expected_log_level

@pytest.mark.parametrize("log_level", [logging.DEBUG, logging.INFO])
def test_set_command_logging(log_level):
    bootstrap_speedwagon.set_command_logging(level=log_level)
    assert speedwagon.startup.logger.getEffectiveLevel() == log_level

def test_run_speedwagon_sub_command():
    args = Mock()
    args.command = "run"
    run_strategy = Mock()
    bootstrap_speedwagon.run_speedwagon_sub_command(args, run_strategy)
    run_strategy.assert_called_once()

def test_run_speedwagon_sub_command_logs_broken_pip(caplog):
    args = Mock()
    args.command = "run"
    run_strategy = Mock(side_effect=BrokenPipeError)
    with pytest.raises(BrokenPipeError):
        bootstrap_speedwagon.run_speedwagon_sub_command(args, run_strategy)

    assert caplog.records[0].levelname == "ERROR"