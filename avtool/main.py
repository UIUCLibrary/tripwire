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
    prog_bar_format = (
        "{desc}{percentage:3.0f}% |{bar}| Time Remaining: {remaining}"
    )

    def print_progress(bar, value: float) -> None:
        bar.set_progress(value)

    for i, file_path in enumerate(args.files):
        progress_bar = ProgressBar(
            total=100.0, leave=False, bar_format=prog_bar_format
        )

        progress_bar.set_description(file_path.name)
        result = validation.get_file_hash(
            file_path,
            hashing_algorithm=SUPPORTED_ALGORITHMS[args.hashing_algorithm],
            progress_reporter=lambda value,  # type: ignore[misc]
            prog_bar=progress_bar: print_progress(prog_bar, value),
        )
        progress_bar.close()

        # Report the results
        if len(args.files) == 1:
            pre_fix = ""
        else:
            pre_fix = f"({i+1}/{len(args.files)}) "
        print(f"{pre_fix}{file_path} --> {args.hashing_algorithm}: {result}")


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
