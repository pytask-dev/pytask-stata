from __future__ import annotations

from contextlib import ExitStack as does_not_raise  # noqa: N813

import pytest
from pytask import Mark
from pytask_stata.collect import _parse_stata_mark
from pytask_stata.collect import stata


@pytest.mark.unit
@pytest.mark.parametrize(
    "args, kwargs, expectation, expected",
    [
        ((), {}, pytest.raises(RuntimeError, match="The old syntax"), None),
        (
            ("-o"),
            {"script": "script.do"},
            pytest.raises(RuntimeError, match="The old syntax"),
            None,
        ),
        (
            (),
            {"options": ("-o")},
            pytest.raises(RuntimeError, match="The old syntax"),
            None,
        ),
        (
            (),
            {"script": "script.do", "options": "--option"},
            does_not_raise(),
            ("script.do", ["--option"]),
        ),
        (
            (),
            {"script": "script.do", "options": [1]},
            does_not_raise(),
            ("script.do", ["1"]),
        ),
    ],
)
def test_stata(args, kwargs, expectation, expected):
    with expectation:
        options = stata(*args, **kwargs)
        assert options == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "mark, expectation, expected",
    [
        (
            Mark("stata", (), {}),
            pytest.raises(RuntimeError, match="The old syntax for @pytask.mark.stata"),
            Mark("stata", (), {"script": None, "options": []}),
        ),
        (
            Mark("stata", ("-o"), {}),
            pytest.raises(RuntimeError, match="The old syntax for @pytask.mark.stata"),
            None,
        ),
        (
            Mark("stata", (), {"script": "script.do"}),
            does_not_raise(),
            Mark("stata", (), {"script": "script.do", "options": []}),
        ),
    ],
)
def test_parse_stata_mark(
    mark,
    expectation,
    expected,
):
    with expectation:
        out = _parse_stata_mark(mark)
        assert out == expected
