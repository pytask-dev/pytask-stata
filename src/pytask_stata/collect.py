"""Collect tasks."""
import copy
import functools
import subprocess
import sys
from pathlib import Path
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
    if get_specific_markers_from_task(task, "stata"):
        source = _get_node_from_dictionary(
            task.depends_on, session.config["stata_source_key"]
        )
        if not (isinstance(source, FilePathNode) and source.value.suffix == ".do"):
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


def _get_node_from_dictionary(obj, key, fallback=0):
    if isinstance(obj, Path):
        pass
    elif isinstance(obj, dict):
        obj = obj.get(key) or obj.get(fallback)
    return obj


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
    source = _get_node_from_dictionary(
        task.depends_on, session.config["stata_source_key"]
    )

    cmd_options = [
        session.config["stata"],
        "-e",
        "do",
        source.value.as_posix(),
        *args,
    ]
    if sys.platform == "win32":
        log_name = convert_task_id_to_name_of_log_file(task.name)
        cmd_options.append(f"-{log_name}")

    return cmd_options
