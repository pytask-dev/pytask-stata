"""Everything related to the CLI."""

from __future__ import annotations

import click
from pytask import hookimpl


@hookimpl
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Add stata related options to the command line interface."""
    additional_parameters = [
        click.Option(
            ["--stata-keep-log"],
            help="Do not remove the log files produced while running do-files.",
            is_flag=True,
        ),
        click.Option(
            ["--stata-check-log-lines"],
            help=(
                "Number of lines of the log file to consider when searching for "
                "non-zero exit codes."
            ),
            type=click.IntRange(min=1),
            default=10,
        ),
    ]
    cli.commands["build"].params.extend(additional_parameters)
