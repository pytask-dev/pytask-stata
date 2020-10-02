"""Collect tasks."""
import copy
import functools
import subprocess
from typing import Iterable
from typing import Optional
from typing import Union

from _pytask.config import hookimpl
from _pytask.mark import get_specific_markers_from_task
from _pytask.mark import has_marker
from _pytask.nodes import FilePathNode
from _pytask.nodes import PythonFunctionTask
from _pytask.parametrize import _copy_func
from pytask_stata.shared import convert_task_id_to_name_of_log_file


def stata(options: Optional[Union[str, Iterable[str]]] = None):
    """Specify command line options for Stata.

    Parameters
    ----------
    options : Optional[Union[str, Iterable[str]]]
        One or multiple command line options passed to Stata.

    """
    if options is None:
        options = []
    elif isinstance(options, str):
        options = [options]
    return options


def run_stata_script(stata):
    """Run an R script."""
    subprocess.run(stata, check=True)


@hookimpl
def pytask_collect_task(session, path, name, obj):
    """Collect a task which is a function.

    There is some discussion on how to detect functions in this `thread
    <https://stackoverflow.com/q/624926/7523785>`_. :class:`types.FunctionType` does not
    detect built-ins which is not possible anyway.

    """
    if name.startswith("task_") and callable(obj) and has_marker(obj, "stata"):
        task = PythonFunctionTask.from_path_name_function_session(
            path, name, obj, session
        )

        return task


@hookimpl
def pytask_collect_task_teardown(session, task):
    """Perform some checks and prepare the task function."""
    if task is not None and get_specific_markers_from_task(task, "stata"):
        if (len(task.depends_on) == 0) or (
            not (
                isinstance(task.depends_on[0], FilePathNode)
                and task.depends_on[0].value.suffix == ".do"
            )
        ):
            raise ValueError(
                "The first dependency of a Stata task must be the do-file."
            )

        stata_function = _copy_func(run_stata_script)
        stata_function.pytaskmark = copy.deepcopy(task.function.pytaskmark)

        merged_marks = _merge_all_markers(task)
        args = stata(*merged_marks.args, **merged_marks.kwargs)
        options = _prepare_cmd_options(session, task, args)
        stata_function = functools.partial(stata_function, stata=options)

        task.function = stata_function


def _merge_all_markers(task):
    """Combine all information from markers for the Stata function."""
    stata_marks = get_specific_markers_from_task(task, "stata")
    mark = stata_marks[0]
    for mark_ in stata_marks[1:]:
        mark = mark.combined_with(mark_)
    return mark


def _prepare_cmd_options(session, task, args):
    """Prepare the command line arguments to execute the do-file.

    The last entry changes the name of the log file. We take the task id as a name which
    is unique and does not cause any errors when parallelizing the execution.

    """
    log_name = convert_task_id_to_name_of_log_file(task.name)
    return [
        session.config["stata"],
        "-e",
        "do",
        task.depends_on[0].value.as_posix(),
        *args,
        f"-{log_name}",
    ]
