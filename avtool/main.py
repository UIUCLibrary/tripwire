import argparse
import hashlib
import pathlib
from avtool import validation

SUPPORTED_ALGORITHMS = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
}


def get_hash_command(args: argparse.Namespace) -> None:
    def print_progress(value: float) -> None:
        print(f"\rProgress: {value:.1f}%", end="")

    result = validation.get_file_hash(
        args.file_path,
        hashing_algorithm=SUPPORTED_ALGORITHMS[args.hashing_algorithm],
        progress_reporter=print_progress,
    )
    print(f"\n{args.file_path} -> {result}")


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub_commands = parser.add_subparsers(
        title="subcommands", required=True, dest="subcommand"
    )
    get_hash_command_parser = sub_commands.add_parser("get-hash")
    get_hash_command_parser.add_argument("file_path", type=pathlib.Path)
    get_hash_command_parser.add_argument(
        "--hashing_algorithm",
        type=str,
        default="md5",
        choices=SUPPORTED_ALGORITHMS.keys(),
    )
    return parser


def main():
    parser = get_arg_parser()
    args = parser.parse_args()
    if args.subcommand == "get-hash":
        get_hash_command(args)


if __name__ == "__main__":
    main()
