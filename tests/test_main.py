import pytest
from avtool import main


@pytest.mark.parametrize(
    "cli_args,expected_subcommand", [(["get-hash", "value"], "get-hash")]
)
def test_sub_commands(cli_args, expected_subcommand):
    args = main.get_arg_parser().parse_args(cli_args)
    assert args.subcommand == expected_subcommand
