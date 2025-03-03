import importlib.metadata
import io
from unittest.mock import Mock, MagicMock
import pytest
from uiucprescon.tripwire import utils


def test_get_version():
    version_strategy = Mock(return_value="1.2.3")
    utils.get_version([version_strategy])
    version_strategy.assert_called_once()


def test_get_version_default_strategy_uses_module_constant(monkeypatch):
    utils.DEFAULT_VERSION_RESOLUTION_STRATEGY_ORDER = MagicMock()
    utils.DEFAULT_VERSION_RESOLUTION_STRATEGY_ORDER.__iter__.return_value = (
        iter([Mock(return_value="1.2.3")])
    )
    utils.get_version()
    utils.DEFAULT_VERSION_RESOLUTION_STRATEGY_ORDER.__iter__.assert_called()


def test_get_version_resolution_order_runs_until_first_valid():
    valid_version_strategy = Mock(return_value="1.2.3")
    invalid_version_strategy = Mock(side_effect=utils.InvalidVersionStrategy)
    uncalled_version_strategy = Mock()

    resolution_order = [
        invalid_version_strategy,
        valid_version_strategy,
        uncalled_version_strategy,
    ]

    assert all(
        [
            utils.get_version(resolution_order) == "1.2.3",
            invalid_version_strategy.called,
            valid_version_strategy.called,
            not uncalled_version_strategy.called,
        ]
    )


def test_get_version_fail():
    with pytest.raises(utils.MissingVersionInformation):
        utils.get_version(resolution_order=[])


def test_get_package_version(monkeypatch):
    monkeypatch.setattr(utils, "version", Mock(return_value="1.2.3"))
    assert utils.get_package_version() == "1.2.3"


def test_get_package_version_no_package_throws(monkeypatch):
    monkeypatch.setattr(
        utils,
        "version",
        Mock(side_effect=importlib.metadata.PackageNotFoundError),
    )
    with pytest.raises(utils.InvalidVersionStrategy):
        utils.get_package_version()


def test_get_version_from_pyproject():
    data = io.BytesIO(
        b"""[project]
        version = "0.2.0"
        \n"""
    )

    pyproject_toml = Mock(
        open=Mock(
            name="open",
            return_value=MagicMock(
                __enter__=Mock(name="read", return_value=data)
            ),
        )
    )
    assert utils.get_version_from_pyproject(path=pyproject_toml) == "0.2.0"


def test_get_version_from_pyproject_not_a_file_failing():
    pyproject_toml = Mock(is_file=Mock(return_value=False))
    with pytest.raises(utils.InvalidVersionStrategy):
        utils.get_version_from_pyproject(path=pyproject_toml)


def test_get_version_from_pyproject_fail():
    data = io.BytesIO(
        b"""[project]
        \n"""
    )

    pyproject_toml = Mock(
        open=Mock(
            name="open",
            return_value=MagicMock(
                __enter__=Mock(name="read", return_value=data)
            ),
        )
    )
    with pytest.raises(utils.InvalidVersionStrategy):
        utils.get_version_from_pyproject(path=pyproject_toml)
