"""Collect tasks."""

from __future__ import annotations

import functools
import subprocess
import warnings
from pathlib import Path
from typing import Any

from pytask import Mark
from pytask import NodeInfo
from pytask import PathNode
from pytask import PTask
from pytask import PythonNode
from pytask import Session
from pytask import Task
from pytask import TaskWithoutPath
from pytask import has_mark
from pytask import hookimpl
from pytask import is_task_function
from pytask import parse_dependencies_from_task_function
from pytask import parse_products_from_task_function
from pytask import remove_marks

from pytask_stata.shared import convert_task_id_to_name_of_log_file
from pytask_stata.shared import stata


def run_stata_script(
    _executable: str,
    _script: Path,
    _options: list[str],
    _log_name: str,
    _cwd: Path,
) -> None:
    """Run an R script."""
    cmd = [_executable, "-e", "do", _script.as_posix(), *_options, f"-{_log_name}"]
    print("Executing " + " ".join(cmd) + ".")  # noqa: T201
    subprocess.run(cmd, cwd=_cwd, check=True)  # noqa: S603


@hookimpl
def pytask_collect_task(
    session: Session, path: Path, name: str, obj: Any
) -> Task | None:
    """Perform some checks and prepare the task function."""
    __tracebackhide__ = True

    if (
        (name.startswith("task_") or has_mark(obj, "task"))
        and is_task_function(obj)
        and has_mark(obj, "stata")
    ):
        # Parse the @pytask.mark.stata decorator.
        obj, marks = remove_marks(obj, "stata")
        if len(marks) > 1:
            msg = (
                f"Task {name!r} has multiple @pytask.mark.stata marks, but only one is "
                "allowed."
            )
            raise ValueError(msg)

        mark = _parse_stata_mark(mark=marks[0])
        script, options = stata(**marks[0].kwargs)
        obj.pytask_meta.markers.append(mark)

        # Collect the nodes in @pytask.mark.julia and validate them.
        path_nodes = Path.cwd() if path is None else path.parent

        if isinstance(script, str):
            warnings.warn(
                "Passing a string to the @pytask.mark.stata parameter 'script' is "
                "deprecated. Please, use a pathlib.Path instead.",
                stacklevel=1,
            )
            script = Path(script)

        script_node = session.hook.pytask_collect_node(
            session=session,
            path=path_nodes,
            node_info=NodeInfo(
                arg_name="script", path=(), value=script, task_path=path, task_name=name
            ),
        )

        if not (isinstance(script_node, PathNode) and script_node.path.suffix == ".do"):
            msg = (
                "The 'script' keyword of the @pytask.mark.stata decorator must point "
                f"to a file with the .do suffix, but it is {script_node}."
            )
            raise ValueError(msg)

        options_node = session.hook.pytask_collect_node(
            session=session,
            path=path_nodes,
            node_info=NodeInfo(
                arg_name="_options",
                path=(),
                value=options,
                task_path=path,
                task_name=name,
            ),
        )

        executable_node = session.hook.pytask_collect_node(
            session=session,
            path=path_nodes,
            node_info=NodeInfo(
                arg_name="_executable",
                path=(),
                value=session.config["stata"],
                task_path=path,
                task_name=name,
            ),
        )

        cwd_node = session.hook.pytask_collect_node(
            session=session,
            path=path_nodes,
            node_info=NodeInfo(
                arg_name="_cwd",
                path=(),
                value=path.parent.as_posix(),
                task_path=path,
                task_name=name,
            ),
        )

        dependencies = parse_dependencies_from_task_function(
            session, path, name, path_nodes, obj
        )
        products = parse_products_from_task_function(
            session, path, name, path_nodes, obj
        )

        # Add script
        dependencies["_script"] = script_node
        dependencies["_options"] = options_node
        dependencies["_cwd"] = cwd_node
        dependencies["_executable"] = executable_node

        partialed = functools.partial(run_stata_script, _cwd=path.parent)
        markers = obj.pytask_meta.markers if hasattr(obj, "pytask_meta") else []

        task: PTask
        if path is None:
            task = TaskWithoutPath(
                name=name,
                function=partialed,
                depends_on=dependencies,
                produces=products,
                markers=markers,
            )
        else:
            task = Task(
                base_name=name,
                path=path,
                function=partialed,
                depends_on=dependencies,
                produces=products,
                markers=markers,
            )

        # Add log_name node that depends on the task id.
        if session.config["platform"] == "win32":
            log_name = convert_task_id_to_name_of_log_file(task)
        else:
            log_name = ""

        log_name_node = session.hook.pytask_collect_node(
            session=session,
            path=path_nodes,
            node_info=NodeInfo(
                arg_name="_log_name",
                path=(),
                value=PythonNode(value=log_name),
                task_path=path,
                task_name=name,
            ),
        )
        task.depends_on["_log_name"] = log_name_node

        return task
    return None


def _parse_stata_mark(mark: Mark) -> Mark:
    """Parse a Stata mark."""
    script, options = stata(**mark.kwargs)
    parsed_kwargs = {"script": script or None, "options": options or []}
    return Mark("stata", (), parsed_kwargs)
