"""Everything related to the CLI."""
import click
from _pytask.config import hookimpl


@hookimpl
def pytask_extend_command_line_interface(cli):
    """Add stata related options to the command line interface."""
    additional_parameters = [
        click.Option(
            ["--stata-keep-log"],
            help=(
                "Do not remove the log files produced while running do-files.  "
                "[default: False]"
            ),
            is_flag=True,
            default=None,
        ),
        click.Option(
            ["--stata-check-log-lines"],
            help=(
                "Number of lines of the log file to consider when searching for "
                "non-zero exit codes.  [default: 10]"
            ),
            type=int,
            default=None,
        ),
    ]
    cli.commands["build"].params.extend(additional_parameters)
