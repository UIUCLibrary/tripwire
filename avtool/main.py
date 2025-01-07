import argparse
import hashlib
import multiprocessing
import pathlib

from tqdm import tqdm

from avtool import validation, utils

SUPPORTED_ALGORITHMS = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
}


class ProgressBar(tqdm):
    def __init__(self, total, *args, **kwargs):
        super().__init__(total, *args, **kwargs)
        self.total = total

    def set_progress(self, position: float) -> None:
        if self.n < position:
            self.update(position - self.n)
        elif self.n > position:
            self.n = position
            self.update(0)
        if position == self.total:
            self.refresh()


def get_hash_command(args: argparse.Namespace) -> None:
    progress_bar = ProgressBar(
        total=100.0,
        leave=False,
        bar_format="{percentage:3.0f}% |{bar}| Time Remaining: {remaining}",
    )

    def print_progress(value: float) -> None:
        progress_bar.set_progress(value)

    result = validation.get_file_hash(
        args.file_path,
        hashing_algorithm=SUPPORTED_ALGORITHMS[args.hashing_algorithm],
        progress_reporter=print_progress,
    )
    progress_bar.close()
    print(f"\n{args.file_path} --> {args.hashing_algorithm}: {result}")


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
    get_hash_command_parser.add_argument("file_path", type=pathlib.Path)
    get_hash_command_parser.add_argument(
        "--hashing_algorithm",
        type=str,
        default="md5",
        help="hashing algorithm to use (default: %(default)s)",
        choices=SUPPORTED_ALGORITHMS.keys(),
    )
    return parser


def main() -> None:
    multiprocessing.freeze_support()
    parser = get_arg_parser()
    args = parser.parse_args()
    if args.subcommand == "get-hash":
        get_hash_command(args)


if __name__ == "__main__":
    main()
