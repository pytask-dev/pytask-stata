from __future__ import annotations

from pathlib import Path

import pytest

from pytask_stata.serialization import serialize_keyword_arguments


def test_yaml_serialization_preserves_unicode(tmp_path):
    path_to_serialized = tmp_path / "config.yaml"

    serialize_keyword_arguments(
        "yaml",
        path_to_serialized,
        {"path": Path("J\u00f6rg")},
    )

    serialized = path_to_serialized.read_text(encoding="utf-8")
    assert "J\u00f6rg" in serialized
    assert r"\xF6" not in serialized


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"items": []},
        {"nested": {"items": []}},
        {"nested": {}},
    ],
)
def test_yaml_serialization_rejects_empty_collections(tmp_path, kwargs):
    with pytest.raises(ValueError, match="Empty YAML"):
        serialize_keyword_arguments("yaml", tmp_path / "config.yaml", kwargs)
