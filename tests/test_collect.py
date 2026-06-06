from __future__ import annotations

from contextlib import ExitStack as does_not_raise  # noqa: N813

import pytest
from pytask import Mark

from pytask_stata.collect import _parse_stata_mark
from pytask_stata.collect import stata


@pytest.mark.parametrize(
    ("args", "kwargs", "expectation", "expected"),
    [
        (
            (),
            {"script": "script.do", "options": "--option"},
            does_not_raise(),
            ("script.do", ["--option"], None, None),
        ),
        (
            (),
            {"script": "script.do", "options": [1]},
            does_not_raise(),
            ("script.do", ["1"], None, None),
        ),
        (
            (),
            {"script": "script.do"},
            does_not_raise(),
            ("script.do", None, None, None),
        ),
    ],
)
def test_stata(args, kwargs, expectation, expected):
    with expectation:
        options = stata(*args, **kwargs)
        assert options == expected


@pytest.mark.parametrize(
    ("mark", "expectation", "expected"),
    [
        (
            Mark("stata", (), {"script": "script.do"}),
            does_not_raise(),
            Mark(
                "stata",
                (),
                {
                    "script": "script.do",
                    "options": None,
                    "serializer": "yaml",
                    "suffix": ".yaml",
                },
            ),
        ),
        (
            Mark("stata", (), {"script": "script.do", "options": []}),
            does_not_raise(),
            Mark(
                "stata",
                (),
                {
                    "script": "script.do",
                    "options": [],
                    "serializer": None,
                    "suffix": None,
                },
            ),
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


def test_parse_stata_mark_with_yaml():
    mark = Mark("stata", (), {"script": "script.do", "serializer": "yaml"})

    out = _parse_stata_mark(mark)

    assert out == Mark(
        "stata",
        (),
        {
            "script": "script.do",
            "options": None,
            "serializer": "yaml",
            "suffix": ".yaml",
        },
    )


def test_parse_stata_mark_raises_for_json():
    mark = Mark("stata", (), {"script": "script.do", "serializer": "json"})

    with pytest.raises(ValueError, match="Serializer 'json' is not known"):
        _parse_stata_mark(mark)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"script": "script.do", "options": [], "serializer": "yaml"},
        {"script": "script.do", "options": [], "suffix": ".yaml"},
    ],
)
def test_parse_stata_mark_raises_for_mixed_interfaces(kwargs):
    mark = Mark("stata", (), kwargs)

    with pytest.raises(ValueError, match="interfaces cannot be mixed"):
        _parse_stata_mark(mark)
