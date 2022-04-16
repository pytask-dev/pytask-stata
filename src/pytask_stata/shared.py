"""Shared functions and variables."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from typing import Iterable
from typing import Sequence


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


_ERROR_MSG = """The old syntax for @pytask.mark.stata was suddenly deprecated starting \
with pytask-stata v0.2 to provide a better user experience. Thank you for your \
understanding!

It is recommended to upgrade to the new syntax, so you enjoy all the benefits of v0.2 \
of pytask and pytask-stata.

You can find a manual here: \
https://github.com/pytask-dev/pytask-stata/blob/v0.2.0/README.md

Upgrading can be as easy as rewriting your current task from

    @pytask.mark.stata(["--option", "path_to_dependency.txt"])
    @pytask.mark.depends_on("script.do")
    @pytask.mark.produces("out.csv")
    def task_r():
        ...

to

    @pytask.mark.stata(script="script.do", options="--option")
    @pytask.mark.depends_on("path_to_dependency.txt")
    @pytask.mark.produces("out.csv")
    def task_r():
        ...

You can also fix the version of pytask and pytask-stata to <0.2, so you do not have to \
to upgrade. At the same time, you will not enjoy the improvements released with \
version v0.2 of pytask and pytask-stata.

"""


def stata(
    *args: Any,
    script: str | Path | None = None,
    options: str | Iterable[str] | None = None,
) -> tuple[str | Path | None, str | Iterable[str] | None]:
    """Specify command line options for Stata.

    Parameters
    ----------
    options : str | Iterable[str] | None
        One or multiple command line options passed to Stata.

    """
    if args or script is None:
        raise RuntimeError(_ERROR_MSG)

    options = [] if options is None else list(map(str, _to_list(options)))
    return script, options


def convert_task_id_to_name_of_log_file(id_: str) -> str:
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
    id_without_parent_directories = id_.rsplit("/")[-1]
    converted_id = id_without_parent_directories.replace(".", "_").replace("::", "_")
    return converted_id


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
