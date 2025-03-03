import argparse
import functools
import logging
import multiprocessing
import pathlib
from typing import Callable, Any

from uiucprescon.tripwire import validation, utils


def capture_log(
    logger: logging.Logger,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            logger.addHandler(handler)
            try:
                return func(*args, **kwargs)
            finally:
                logger.removeHandler(handler)

        return wrapper

    return decorator


@capture_log(logger=validation.logger)
def get_hash_command(args: argparse.Namespace) -> None:
    validation.get_hash_command(
        files=args.files, hashing_algorithm=args.hashing_algorithm
    )


@capture_log(logger=validation.logger)
def validate_checksums_command(args: argparse.Namespace) -> None:
    validation.validate_directory_checksums_command(path=args.path)


def get_arg_parser() -> argparse.ArgumentParser:
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

    return parser


def main() -> None:
    multiprocessing.freeze_support()
    parser = get_arg_parser()
    args = parser.parse_args()
    match args.subcommand:
        case "get-hash":
            get_hash_command(args)
        case "validate-checksums":
            validate_checksums_command(args)


if __name__ == "__main__":
    main()
