"""Execute tasks."""

from __future__ import annotations

import re
from pathlib import Path

from pytask import PTask
from pytask import PTaskWithPath
from pytask import Session
from pytask import has_mark
from pytask import hookimpl

from pytask_stata.shared import STATA_COMMANDS


@hookimpl
def pytask_execute_task_setup(session: Session, task: PTask) -> None:
    """Check if Stata is found on the PATH."""
    if has_mark(task, "stata") and session.config["stata"] is None:
        msg = (
            "Stata is needed to run do-files, but it is not found on your PATH.\n\n"
            f"We are looking for one of {STATA_COMMANDS} on your PATH. If you have a"
            "different Stata executable, please, file an issue at "
            "https://github.com/pytask-dev/pytask-stata."
        )
        raise RuntimeError(msg)


@hookimpl
def pytask_execute_task_teardown(session: Session, task: PTask) -> None:
    """Check if the log file contains no error code.

    Stata has the weird behavior of always returning an exit code of 0 even if an error
    occurred. Therefore, we need to parse the real error code from the log files.

    Error codes have a preceding r and a number enclosed in round brackets like ``r(1)``
    or ``r(601)``.

    """
    if has_mark(task, "stata"):
        if session.config["platform"] == "win32":
            log_name = task.depends_on["_log_name"].load()
            if isinstance(task, PTaskWithPath):
                path_to_log = task.path.with_name(log_name).with_suffix(".log")
            else:
                path_to_log = Path.cwd(log_name).with_name(log_name).with_suffix(".log")
        else:
            node = task.depends_on["_script"]
            path_to_log = node.path.with_suffix(".log")

        n_lines = session.config["stata_check_log_lines"]

        log = path_to_log.read_text()
        log_tail = log.split("\n")[-n_lines:]
        for line in log_tail:
            error_found = re.match(r"r\(([0-9]+)\)", line)

            if error_found:
                if not session.config["stata_keep_log"]:
                    path_to_log.unlink()

                raise RuntimeError(
                    f"An error occurred. Here are the last {n_lines} lines of the log:"
                    "\n\n" + "\n".join(log_tail)
                )
