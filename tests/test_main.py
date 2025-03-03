import pytest
from uiucprescon.tripwire import main


@pytest.mark.parametrize(
    "cli_args,expected_subcommand", [(["get-hash", "value"], "get-hash")]
)
def test_sub_commands(cli_args, expected_subcommand):
    args = main.get_arg_parser().parse_args(cli_args)
    assert args.subcommand == expected_subcommand


def test_calling_version_flag_exits_with_zero():
    with pytest.raises(SystemExit) as e:
        main.get_arg_parser().parse_args(["--version"])
    assert e.value.code == 0


@pytest.mark.parametrize(
    "cli_args, expected_files",
    [
        (["get-hash", "file1.wav", "file2.wav"], ["file1.wav", "file2.wav"]),
        (
            [
                "get-hash",
                "--hashing_algorithm=sha256",
                "file1.wav",
                "file2.wav",
            ],
            ["file1.wav", "file2.wav"],
        ),
        (["get-hash", "file1.wav"], ["file1.wav"]),
    ],
)
def test_get_hash_file_args(cli_args, expected_files):
    args = main.get_arg_parser().parse_args(cli_args)
    assert [str(f) for f in args.files] == expected_files
