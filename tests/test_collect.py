from __future__ import annotations

from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path

import pytest
from _pytask.mark import Mark
from _pytask.nodes import FilePathNode
from pytask_stata.collect import _merge_all_markers
from pytask_stata.collect import _prepare_cmd_options
from pytask_stata.collect import pytask_collect_task_teardown
from pytask_stata.collect import stata
from pytask_stata.shared import get_node_from_dictionary


class DummyClass:
    pass


def task_dummy():
    pass


@pytest.mark.unit
@pytest.mark.parametrize(
    "stata_args, expected",
    [
        (None, []),
        ("some-arg", ["some-arg"]),
        (["arg1", "arg2"], ["arg1", "arg2"]),
    ],
)
def test_stata(stata_args, expected):
    options = stata(stata_args)
    assert options == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "marks, expected",
    [
        (
            [Mark("stata", ("a",), {}), Mark("stata", ("b",), {})],
            Mark("stata", ("a", "b"), {}),
        ),
        (
            [Mark("stata", ("a",), {}), Mark("stata", (), {"stata": "b"})],
            Mark("stata", ("a",), {"stata": "b"}),
        ),
    ],
)
def test_merge_all_markers(marks, expected):
    task = DummyClass()
    task.markers = marks
    out = _merge_all_markers(task)
    assert out == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "args",
    [
        [],
        ["a"],
        ["a", "b"],
    ],
)
@pytest.mark.parametrize("stata_source_key", ["source", "do"])
@pytest.mark.parametrize("platform", ["win32", "linux", "darwin"])
def test_prepare_cmd_options(args, stata_source_key, platform):
    session = DummyClass()
    session.config = {
        "stata": "stata",
        "stata_source_key": stata_source_key,
        "platform": platform,
    }

    node = DummyClass()
    node.path = Path("script.do")
    task = DummyClass()
    task.depends_on = {stata_source_key: node}
    task.name = "task"

    result = _prepare_cmd_options(session, task, args)

    expected = [
        "stata",
        "-e",
        "do",
        "script.do",
        *args,
    ]
    if platform == "win32":
        expected.append("-task")

    assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "depends_on, produces, expectation",
    [
        (["script.do"], ["any_out.dta"], does_not_raise()),
        (["script.txt"], ["any_out.dta"], pytest.raises(ValueError)),
        (["input.dta", "script.do"], ["any_out.dta"], pytest.raises(ValueError)),
    ],
)
@pytest.mark.parametrize("platform", ["win32", "darwin", "linux"])
def test_pytask_collect_task_teardown(
    tmp_path, depends_on, produces, platform, expectation
):
    session = DummyClass()
    session.config = {
        "stata": "stata",
        "stata_source_key": "source",
        "platform": platform,
    }

    task = DummyClass()
    task.depends_on = {
        i: FilePathNode.from_path(tmp_path / n) for i, n in enumerate(depends_on)
    }
    task.produces = {
        i: FilePathNode.from_path(tmp_path / n) for i, n in enumerate(produces)
    }
    task.function = task_dummy
    task.name = "task_dummy"
    task.path = Path()

    markers = [Mark("stata", (), {})]
    task.markers = markers
    task.function.pytaskmark = markers

    with expectation:
        pytask_collect_task_teardown(session, task)


@pytest.mark.unit
@pytest.mark.parametrize(
    "obj, key, expected",
    [
        (1, "asds", 1),
        (1, None, 1),
        ({"a": 1}, "a", 1),
        ({0: 1}, "a", 1),
    ],
)
def test_get_node_from_dictionary(obj, key, expected):
    result = get_node_from_dictionary(obj, key)
    assert result == expected
