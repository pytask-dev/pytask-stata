"""Execute tasks."""
import re

from _pytask.config import hookimpl
from _pytask.mark import get_specific_markers_from_task
from pytask_stata.shared import convert_task_id_to_name_of_log_file
from pytask_stata.shared import get_node_from_dictionary
from pytask_stata.shared import STATA_COMMANDS


@hookimpl
def pytask_execute_task_setup(session, task):
    """Check if Stata is found on the PATH."""
    if (
        get_specific_markers_from_task(task, "stata")
        and session.config["stata"] is None
    ):
        raise RuntimeError(
            "Stata is needed to run do-files, but it is not found on your PATH.\n\n"
            f"We are looking for one of {STATA_COMMANDS} on your PATH. If you have a"
            "different Stata executable, please, file an issue at "
            "https://github.com/pytask-dev/pytask-stata."
        )


@hookimpl
def pytask_execute_task_teardown(session, task):
    """Check if the log file contains no error code.

    Stata has the weird behavior of always returning an exit code of 0 even if an error
    occurred. Therefore, we need to parse the real error code from the log files.

    Error codes have a preceding r and a number enclosed in round brackets like ``r(1)``
    or ``r(601)``.

    """
    if get_specific_markers_from_task(task, "stata"):
        if session.config["platform"] == "win32":
            log_name = convert_task_id_to_name_of_log_file(task.name)
            path_to_log = task.path.with_name(log_name).with_suffix(".log")
        else:
            source = get_node_from_dictionary(
                task.depends_on, session.config["stata_source_key"]
            )
            path_to_log = source.path.with_suffix(".log")

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
