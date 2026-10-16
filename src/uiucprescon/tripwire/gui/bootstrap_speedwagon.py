"""This launches a speedwagon application configured to run tripwire."""

import logging
import os
import pathlib
import sys

import argparse
from typing import Dict, List

import speedwagon.startup
import speedwagon.config.config
import speedwagon.tasks.system
from uiucprescon.tripwire.utils import get_version

__all__ = ['run_speedwagon']

# =============================================================================
# ENVIRONMENT_VARIABLE_NAMES

ENVIRONMENT_VAR_NAME_CONFIG_DIRECTORY_NAME = "TRIPWIRE_CONFIG_DIRECTORY_NAME"
# set this environment variable to change the prefix name of config file.
# Note: It will still in the home directory, just with a different name other
# than the default


# =============================================================================
#  Defaults

DEFAULT_CONFIG_DIRECTORY_NAME = "tripwire-speedwagon"

# =============================================================================

# Constants
DEFAULT_CONFIG_DATA = """
[GLOBAL]
starting-tab = All
debug = False

[PLUGINS.uiucprescon.tripwire.speedwagon_plugin.plugin]
tripwire_workflows = True

""".strip()
#
# DEFAULT_TABS_DATA = """
# """.strip()
DEFAULT_TABS_DATA = """
Checksum:
- Get-Hash
- validate-checksums
Manifest:
- manifest-check
Metadata:
- metadata-show
- metadata-validate
""".strip()

bootstrap_logger = logging.getLogger("bootstrap_speedwagon")


def write_config_file(config_ini: str) -> None:
    with open(config_ini, "w", encoding="utf-8") as f:
        f.write(f"{DEFAULT_CONFIG_DATA}\n")


def verify_plugin_start(
    config_ini: str,
    write_config_strategy=write_config_file
) -> None:
    """Create boilerplate config file if not already present."""
    app_data_directory = os.path.dirname(config_ini)
    if not os.path.exists(app_data_directory):
        os.makedirs(app_data_directory)

    if not os.path.exists(config_ini):
        bootstrap_logger.info(f"Creating a new config file: {config_ini}")
        write_config_strategy(config_ini)


def write_tabs_file(location: str):
    with pathlib.Path(location).open("w", encoding="utf-8") as fp:
        fp.write(f"{DEFAULT_TABS_DATA}\n")


def set_tabs(
    config_file_location: Dict[str, str],
    write_file_strategy=write_tabs_file
) -> None:
    """Create customized tabs file if not already present."""
    tab_file = config_file_location["tab_config_file"]
    if not os.path.exists(tab_file):
        bootstrap_logger.info(f"Creating initial tabs file: {tab_file}")
        write_file_strategy(tab_file)


DEFAULT_STARTUP_TASKS = [
    lambda _, config_file_location: verify_plugin_start(
        os.path.join(
            config_file_location['app_data_directory'],
            speedwagon.config.config.CONFIG_INI_FILE_NAME
        ),
    ),
    lambda _, config_file_location: set_tabs(config_file_location),
]


def get_arg_parser():
    speedwagon_parser = speedwagon.config.config.CliArgsSetter.get_arg_parser()
    parser = argparse.ArgumentParser(
        description=__doc__,
        parents=[speedwagon_parser],
        conflict_handler="resolve",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {get_version()}"
    )
    return parser


def setup_bootstrap_logger(argv: List[str]):
    if "--verbose" in argv:
        logging_level = logging.DEBUG

        # IMPORTANT: The current line is there because without it, arg parse
        # will fail because "--verbose" is not a flag being used by
        # speedwagon. If we even support the "--verbose" flag in anything
        # else, please remove the following line.
        argv.remove("--verbose")
    else:
        logging_level = logging.INFO

    bootstrap_logger.setLevel(logging_level)
    bootstrap_log_handler = logging.StreamHandler(sys.stderr)

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    bootstrap_log_handler.setFormatter(formatter)

    bootstrap_logger.addHandler(bootstrap_log_handler)


def set_command_logging(level=logging.INFO):
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(level)
    stdout_handler.addFilter(lambda rec: rec.levelno < logging.WARNING)
    speedwagon.startup.logger.addHandler(stdout_handler)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    speedwagon.startup.logger.addHandler(stderr_handler)

    speedwagon.startup.logger.setLevel(level)


def run_speedwagon_sub_command(
    args,
    run_strategy=speedwagon.startup.run_command
):
    set_command_logging()
    try:
        run_strategy(
            command_name=args.command, args=args,
            config_dir=DEFAULT_CONFIG_DIRECTORY_NAME
        )
    except BrokenPipeError:
        bootstrap_logger.error("Broken pipe error here")
        raise
    return 0


def ensure_required_files_exist():
    config_file_location = speedwagon.config.get_platform_settings(
        prefix=DEFAULT_CONFIG_DIRECTORY_NAME
    )
    app_directory = config_file_location.get_app_data_directory()
    if not os.path.exists(app_directory):
        os.makedirs(app_directory)

    config_file = os.path.join(
        app_directory,
        speedwagon.config.config.CONFIG_INI_FILE_NAME
    )
    if not os.path.exists(config_file):
        write_config_file(config_file)

    tab_file = os.path.join(
        app_directory,
        speedwagon.config.config.TABS_YML_FILE_NAME
    )
    if not os.path.exists(tab_file):
        write_tabs_file(tab_file)


def run_speedwagon(
    argv=None,
    startup_tasks=None,
    app_launcher_klass=speedwagon.startup.ApplicationLauncher,
) -> int:
    """Launch a speedwagon application configured to run tripwire commands."""
    parser = get_arg_parser()
    argv = argv or sys.argv

    setup_bootstrap_logger(argv)
    ensure_required_files_exist()
    args = parser.parse_args(argv[1:])
    if args.command is not None:
        return run_speedwagon_sub_command(args)

    app_launcher = app_launcher_klass()
    app_launcher.application_name = "Tripwire"

    app_launcher.application_config_directory_name = os.getenv(
        ENVIRONMENT_VAR_NAME_CONFIG_DIRECTORY_NAME,
        DEFAULT_CONFIG_DIRECTORY_NAME,
    )

    app_launcher.startup_tasks = (
        startup_tasks if startup_tasks is not None else DEFAULT_STARTUP_TASKS
    )

    bootstrap_logger.debug("Initializing Speedwagon")
    app_launcher.initialize()
    bootstrap_logger.debug("Initializing Speedwagon - Done")
    bootstrap_logger.debug("Running Speedwagon with tripwire configured...")
    try:
        return app_launcher.run()
    finally:
        bootstrap_logger.debug("Speedwagon closed")
