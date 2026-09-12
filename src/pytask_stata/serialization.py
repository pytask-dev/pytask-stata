"""Serialize task keyword arguments for Stata do-files."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any
from typing import TypedDict

import yaml
from pytask import PTask
from pytask import PTaskWithPath

__all__ = ["SERIALIZERS", "create_path_to_serialized", "serialize_keyword_arguments"]

_HIDDEN_FOLDER = ".pytask/pytask-stata"

SerializerFunc = Callable[..., str]


class SerializerEntry(TypedDict):
    """Describe a serializer function and its output suffix."""

    serializer: SerializerFunc
    suffix: str


def _dump_yaml(kwargs: dict[str, Any]) -> str:
    """Serialize task keyword arguments as YAML."""
    _validate_yaml_collections(kwargs)
    return yaml.safe_dump(kwargs, sort_keys=False, allow_unicode=True)


def _validate_yaml_collections(value: Any, path: str = "<root>") -> None:
    """Reject empty collections unsupported by the Stata YAML parser."""
    if isinstance(value, dict):
        if not value:
            msg = f"Empty YAML mapping at {path} is not supported."
            raise ValueError(msg)
        for key, item in value.items():
            _validate_yaml_collections(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        if not value:
            msg = f"Empty YAML list at {path} is not supported."
            raise ValueError(msg)
        for index, item in enumerate(value):
            _validate_yaml_collections(item, f"{path}[{index}]")


SERIALIZERS: dict[str, SerializerEntry] = {
    "yaml": {"serializer": _dump_yaml, "suffix": ".yaml"},
    "yml": {"serializer": _dump_yaml, "suffix": ".yml"},
}


def create_path_to_serialized(task: PTask, suffix: str) -> Path:
    """Create path to serialized task data."""
    return (
        (task.path.parent if isinstance(task, PTaskWithPath) else Path.cwd())
        .joinpath(_HIDDEN_FOLDER, str(uuid.uuid4()))
        .with_suffix(suffix)
    )


def serialize_keyword_arguments(
    serializer: str | SerializerFunc,
    path_to_serialized: Path,
    kwargs: dict[str, Any],
) -> None:
    """Serialize keyword arguments."""
    if isinstance(serializer, str):
        if serializer not in SERIALIZERS:
            msg = f"Serializer {serializer!r} is not known."
            raise ValueError(msg)
        serializer_func = SERIALIZERS[serializer]["serializer"]
    elif callable(serializer):
        serializer_func = serializer
    else:
        msg = f"Serializer {serializer!r} is not known."
        raise TypeError(msg)

    serialized = serializer_func(_normalize_for_stata(kwargs))
    path_to_serialized.write_text(serialized, encoding="utf-8")


def _normalize_for_stata(value: Any) -> Any:
    """Normalize values to objects supported by common config serializers."""
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {str(key): _normalize_for_stata(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_for_stata(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_normalize_for_stata(item) for item in value)
    return value
