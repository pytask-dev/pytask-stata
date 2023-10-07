"""Collect tasks."""
from __future__ import annotations

import functools
import subprocess
from types import FunctionType
from typing import Any
from typing import TYPE_CHECKING

from pytask import depends_on
from pytask import has_mark
from pytask import hookimpl
from pytask import Mark
from pytask import parse_nodes
from pytask import produces
from pytask import remove_marks
from pytask import Session
from pytask import Task
from pytask_stata.shared import convert_task_id_to_name_of_log_file
from pytask_stata.shared import stata

if TYPE_CHECKING:
    from pathlib import Path


def run_stata_script(
    executable: str, script: Path, options: list[str], log_name: list[str], cwd: Path
) -> None:
    """Run an R script."""
    cmd = [executable, "-e", "do", script.as_posix(), *options, *log_name]
    print("Executing " + " ".join(cmd) + ".")  # noqa: T201
    subprocess.run(cmd, cwd=cwd, check=True)  # noqa: S603


@hookimpl
def pytask_collect_task(
    session: Session, path: Path, name: str, obj: Any
) -> Task | None:
    """Perform some checks and prepare the task function."""
    __tracebackhide__ = True

    if (
        (name.startswith("task_") or has_mark(obj, "task"))
        and callable(obj)
        and has_mark(obj, "stata")
    ):
        obj, marks = remove_marks(obj, "stata")

        if len(marks) > 1:
            raise ValueError(
                f"Task {name!r} has multiple @pytask.mark.stata marks, but only one is "
                "allowed."
            )

        mark = _parse_stata_mark(mark=marks[0])
        script, options = stata(**marks[0].kwargs)

        obj.pytask_meta.markers.append(mark)

        dependencies = parse_nodes(session, path, name, obj, depends_on)
        products = parse_nodes(session, path, name, obj, produces)

        markers = obj.pytask_meta.markers if hasattr(obj, "pytask_meta") else []
        kwargs = obj.pytask_meta.kwargs if hasattr(obj, "pytask_meta") else {}

        task = Task(
            base_name=name,
            path=path,
            function=_copy_func(run_stata_script),  # type: ignore[arg-type]
            depends_on=dependencies,
            produces=products,
            markers=markers,
            kwargs=kwargs,
        )

        script_node = session.hook.pytask_collect_node(
            session=session, path=path, node=script
        )

        if isinstance(task.depends_on, dict):
            task.depends_on["__script"] = script_node
        else:
            task.depends_on = {0: task.depends_on, "__script": script_node}

        if session.config["platform"] == "win32":
            log_name = convert_task_id_to_name_of_log_file(task.short_name)
            log_name_arg = [f"-{log_name}"]
        else:
            log_name_arg = []

        stata_function = functools.partial(
            task.function,
            executable=session.config["stata"],
            script=task.depends_on["__script"].path,
            options=options,
            log_name=log_name_arg,
            cwd=task.path.parent,
        )

        task.function = stata_function

        return task
    return None


def _parse_stata_mark(mark: Mark) -> Mark:
    """Parse a Stata mark."""
    script, options = stata(**mark.kwargs)

    parsed_kwargs = {"script": script or None, "options": options or []}

    mark = Mark("stata", (), parsed_kwargs)
    return mark


def _copy_func(func: FunctionType) -> FunctionType:
    """Create a copy of a function.

    Based on https://stackoverflow.com/a/13503277/7523785.

    Example
    -------
    >>> def _func(): pass
    >>> copied_func = _copy_func(_func)
    >>> _func is copied_func
    False

    """
    new_func = FunctionType(
        func.__code__,
        func.__globals__,
        name=func.__name__,
        argdefs=func.__defaults__,
        closure=func.__closure__,
    )
    new_func = functools.update_wrapper(new_func, func)
    new_func.__kwdefaults__ = func.__kwdefaults__
    return new_func
