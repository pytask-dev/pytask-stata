"""Shared functions and variables."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING
from typing import Any
from typing import Iterable
from typing import Sequence

if TYPE_CHECKING:
    from pathlib import Path

    from pytask import PTask


if sys.platform == "darwin":
    STATA_COMMANDS = [
        "Stata64MP",
        "StataMP",
        "Stata64SE",
        "StataSE",
        "Stata64",
        "Stata",
    ]
elif sys.platform == "linux":
    STATA_COMMANDS = ["stata-mp", "stata-se", "stata"]
elif sys.platform == "win32":
    STATA_COMMANDS = [
        "StataMP-64",
        "StataMP-ia",
        "StataMP",
        "StataSE-64",
        "StataSE-ia",
        "StataSE",
        "Stata-64",
        "Stata-ia",
        "Stata",
        "WMPSTATA",
        "WSESTATA",
        "WSTATA",
    ]
else:
    STATA_COMMANDS = []


def stata(
    *,
    script: str | Path,
    options: str | Iterable[str] | None = None,
) -> tuple[str | Path | None, str | Iterable[str] | None]:
    """Specify command line options for Stata.

    Parameters
    ----------
    options : str | Iterable[str] | None
        One or multiple command line options passed to Stata.

    """
    options = [] if options is None else list(map(str, _to_list(options)))
    return script, options


def convert_task_id_to_name_of_log_file(task: PTask) -> str:
    """Convert task to id to name of log file.

    If one passes the complete task id as the log file name, Stata would remove parent
    directories and cut the string at the double colons for parametrized task. Here is
    an example:

    .. code-block:: none

        C:/task_example.py::task_example[arg1] -> task_example.log

    This function creates a new id starting from the task module and by replacing dots
    and double colons with underscores.

    Example
    -------
    >>> convert_task_id_to_name_of_log_file("C:/task_example.py::task_example[arg1]")
    'task_example_py_task_example[arg1]'

    """
    id_ = getattr(task, "short_name", task.name)
    return (
        id_.rsplit("/")[-1]
        .replace(".", "_")
        .replace("::", "_")
        .replace("<", "")
        .replace(">", "")
    )


def _to_list(scalar_or_iter: Any) -> list[Any]:
    """Convert scalars and iterables to list.

    Parameters
    ----------
    scalar_or_iter

    Returns
    -------
    list

    Examples
    --------
    >>> _to_list("a")
    ['a']
    >>> _to_list(["b"])
    ['b']

    """
    return (
        [scalar_or_iter]
        if isinstance(scalar_or_iter, str) or not isinstance(scalar_or_iter, Sequence)
        else list(scalar_or_iter)
    )
