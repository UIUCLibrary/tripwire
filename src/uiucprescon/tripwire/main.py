"""Tripwire command line interface."""
# PYTHON_ARGCOMPLETE_OK

import argparse
import functools
import logging
import pathlib
import sys
from typing import Callable, Any, Dict, Tuple, Optional

from uiucprescon.tripwire import validation, utils, manifest_check, metadata
from uiucprescon.tripwire.files import InvalidFileFormat
import argcomplete

logger = logging.getLogger(__name__)


def capture_log(
    logger: logging.Logger,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to capture log messages."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            logger.addHandler(handler)
            try:
                return func(*args, **kwargs)
            finally:
                handler.flush()
                logger.removeHandler(handler)

        return wrapper

    return decorator


@capture_log(logger=validation.logger)
def get_hash_command(args: argparse.Namespace) -> None:
    """Run get hash command."""
    validation.get_hash_command(
        files=args.files, hashing_algorithm=args.hashing_algorithm
    )


@capture_log(logger=validation.logger)
def validate_checksums_command(args: argparse.Namespace) -> None:
    """Run validate checksums command."""
    validation.validate_directory_checksums_command(path=args.path)


@capture_log(logger=manifest_check.logger)
def manifest_check_command(
    args: argparse.Namespace,
    print_usage_function: Callable[[Optional[Any]], None],
) -> None:
    """Run manifest check command."""
    try:
        manifest_check.locate_manifest_files(
            manifest_tsv=args.manifest, search_path=args.search_path
        )
    except InvalidFileFormat as e:
        logger.error(str(e))
        print_usage_function(sys.stderr)
        exit(1)


def get_arg_parser() -> Tuple[
    argparse.ArgumentParser, Dict[str, Callable[[Optional[Any]], None]]
]:
    """Get argument parser for the command line interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {utils.get_version()}",
    )

    sub_commands = parser.add_subparsers(
        title="subcommands", required=True, dest="subcommand"
    )

    get_hash_command_parser = sub_commands.add_parser("get-hash")
    get_hash_command_parser.add_argument("files", nargs="*", type=pathlib.Path)
    get_hash_command_parser.set_defaults(func=get_hash_command)
    get_hash_command_parser.add_argument(
        "--hashing_algorithm",
        type=str,
        default="md5",
        help="hashing algorithm to use (default: %(default)s)",
        choices=validation.SUPPORTED_ALGORITHMS.keys(),
    )

    validate_checksums_parser = sub_commands.add_parser("validate-checksums")
    validate_checksums_parser.add_argument("path", type=pathlib.Path)

    manifest_check_parser = sub_commands.add_parser("manifest-check")
    manifest_check_parser.add_argument(
        "manifest",
        type=pathlib.Path,
        help=""".tsv file that contains a package manifest.
        Note that this is NOT an excel (.xlsx) file. To create a .tsv file,
        from an .xlsx file, open the .xlsx file in Excel and save it as a
        Tab Delimited Text file format.""",
    )
    manifest_check_parser.add_argument(
        "search_path",
        type=pathlib.Path,
        help="Path to search recursively for files listed in the manifest.",
    )
    metadata_cmd = sub_commands.add_parser("metadata")
    metadata_parser = metadata_cmd.add_subparsers(
        dest="metadata_command", required=True
    )

    metadata_show_show = metadata_parser.add_parser(
        "show", help="Show metadata for files."
    )

    metadata_show_show.add_argument("glob", type=str)

    return (
        parser,
        {
            "get-hash": get_hash_command_parser.print_help,
            "validate-checksums": validate_checksums_parser.print_help,
            "manifest-check": manifest_check_parser.print_help,
            "metadata": metadata_cmd.print_help,
        },
    )


@capture_log(logger=metadata.logger)
def metadata_show_command(args: argparse.Namespace) -> None:
    """Run metadata show command."""
    metadata.show_metadata(args.glob, search_path=pathlib.Path("."))


def metadata_command(args: argparse.Namespace, subcommand: str) -> None:
    """Run metadata command."""
    match subcommand:
        case "show":
            metadata_show_command(args)
        case _:
            raise ValueError(f"Unknown metadata subcommand: {subcommand}")


def main() -> None:
    """Main entry point for the Tripwire command line interface."""
    parser, print_help_commands = get_arg_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    match args.subcommand:
        case "get-hash":
            get_hash_command(args)
        case "validate-checksums":
            validate_checksums_command(args)
        case "manifest-check":
            manifest_check_command(
                args,
                print_usage_function=print_help_commands["manifest-check"],
            )
        case "metadata":
            metadata_command(args, args.metadata_command)


if __name__ == "__main__":
    main()
