from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path

import pytest
from _pytask.mark import Mark
from _pytask.nodes import FilePathNode
from pytask_stata.collect import _get_node_from_dictionary
from pytask_stata.collect import _merge_all_markers
from pytask_stata.collect import _prepare_cmd_options
from pytask_stata.collect import pytask_collect_task
from pytask_stata.collect import pytask_collect_task_teardown
from pytask_stata.collect import stata


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
def test_prepare_cmd_options(args, stata_source_key):
    session = DummyClass()
    session.config = {"stata": "stata", "stata_source_key": stata_source_key}

    node = DummyClass()
    node.value = Path("script.do")
    task = DummyClass()
    task.depends_on = {stata_source_key: node}
    task.name = "task"

    result = _prepare_cmd_options(session, task, args)

    assert result == [
        "stata",
        "-e",
        "do",
        "script.do",
        *args,
        "-task",
    ]


@pytest.mark.unit
@pytest.mark.parametrize(
    "name, expected",
    [("task_dummy", True), ("invalid_name", None)],
)
def test_pytask_collect_task(name, expected):
    session = DummyClass()
    session.config = {"stata": "stata"}
    path = Path("some_path")
    task_dummy.pytaskmark = [Mark("stata", (), {})]

    task = pytask_collect_task(session, path, name, task_dummy)

    if expected:
        assert task
    else:
        assert not task


@pytest.mark.unit
@pytest.mark.parametrize(
    "depends_on, produces, expectation",
    [
        (["script.do"], ["any_out.dta"], does_not_raise()),
        (["script.txt"], ["any_out.dta"], pytest.raises(ValueError)),
        (["input.dta", "script.do"], ["any_out.dta"], pytest.raises(ValueError)),
    ],
)
def test_pytask_collect_task_teardown(depends_on, produces, expectation):
    session = DummyClass()
    session.config = {"stata": "stata", "stata_source_key": "source"}

    task = DummyClass()
    task.depends_on = {
        i: FilePathNode(n.split(".")[0], Path(n)) for i, n in enumerate(depends_on)
    }
    task.produces = {
        i: FilePathNode(n.split(".")[0], Path(n)) for i, n in enumerate(produces)
    }
    task.function = task_dummy
    task.name = "task_dummy"

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
    result = _get_node_from_dictionary(obj, key)
    assert result == expected
