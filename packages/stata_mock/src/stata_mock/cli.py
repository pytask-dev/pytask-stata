"""Command line interface for the mock Stata executable."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

INVALID_SYNTAX = 198
UNKNOWN_COMMAND = 199
MINIMUM_ARGUMENTS = 4


def main() -> int:
    """Run a tiny subset of Stata syntax for pytask-stata tests."""
    parsed = _parse_invocation(sys.argv[1:])
    if parsed is None:
        return INVALID_SYNTAX

    script, options, log = parsed
    lines, error_code = _run_script(script, options)

    lines.append(
        f"r({error_code})" if error_code is not None else "end of mock do-file"
    )
    log.write_text("\n".join(lines) + "\n")
    return 0


def _parse_invocation(args: list[str]) -> tuple[Path, list[str], Path] | None:
    if len(args) < MINIMUM_ARGUMENTS or args[:2] != ["-e", "do"]:
        return None

    script = Path(args[2]).resolve()
    options = args[3:-1]
    log_arg = args[-1]
    log = (
        script.with_suffix(".log")
        if log_arg == "-"
        else Path.cwd() / f"{log_arg.removeprefix('-')}.log"
    )
    return script, options, log


def _run_script(script: Path, options: list[str]) -> tuple[list[str], int | None]:
    lines = [f"running mock Stata for {script.name}"]
    state = RuntimeState()

    for raw_line in _iter_stata_lines(script):
        line = raw_line.strip()
        if not line or line.startswith("*"):
            continue

        line = _expand_macros(line, state)
        lines.append(f". {line}")
        error_code = _execute_line(line, state, options)
        if error_code is not None:
            return lines, error_code

    return lines, None


def _iter_stata_lines(script: Path) -> list[str]:
    lines: list[str] = []
    continued = ""
    for raw_line in script.read_text().splitlines():
        stripped = raw_line.rstrip()
        if stripped.endswith("///"):
            continued += stripped.removesuffix("///").rstrip() + " "
            continue
        lines.append(continued + raw_line if continued else raw_line)
        continued = ""
    if continued:
        lines.append(continued)
    return lines


@dataclass
class YamlEntry:
    """A flattened YAML key/value record."""

    key: str
    value: str
    level: int
    parent: str
    type: str


@dataclass
class RuntimeState:
    """Mutable state for a mock Stata do-file run."""

    macros: dict[str, str] = field(default_factory=dict)
    returns: dict[str, str] = field(default_factory=dict)
    yaml_entries: dict[str, YamlEntry] = field(default_factory=dict)


def _execute_line(line: str, state: RuntimeState, options: list[str]) -> int | None:
    command, _, rest = line.partition(" ")
    command = command.lower()
    rest = rest.strip()

    if command == "args":
        state.macros.update(dict(zip(rest.split(), options, strict=False)))
    elif command == "sysuse":
        return None
    elif command == "save":
        return _save_dataset(rest)
    elif command == "yaml":
        return _execute_yaml(rest, state)
    elif command in {"error", "exit"}:
        return int(rest.split()[0])
    else:
        return UNKNOWN_COMMAND

    return None


def _save_dataset(rest: str) -> int | None:
    target = _parse_save_target(rest)
    if not target:
        return INVALID_SYNTAX

    path = Path(target)
    if path.suffix == "":
        path = path.with_suffix(".dta")
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("mock Stata dataset\n")
    return None


def _execute_yaml(rest: str, state: RuntimeState) -> int | None:
    match = re.match(r"(?P<subcommand>\w+)(?P<remaining>.*)", rest)
    if match is None:
        return INVALID_SYNTAX
    subcommand = match.group("subcommand")
    remaining = match.group("remaining")
    subcommand = {"check": "validate", "desc": "describe"}.get(
        subcommand.lower(),
        subcommand.lower(),
    )
    remaining = remaining.strip()

    if subcommand == "read":
        return _yaml_read(remaining, state)
    if subcommand == "get":
        return _yaml_get(remaining, state)
    if subcommand == "validate":
        return _yaml_validate(remaining, state)
    if subcommand in {"describe", "list", "dir", "frames", "clear"}:
        return None
    return UNKNOWN_COMMAND


def _yaml_read(rest: str, state: RuntimeState) -> int | None:
    match = re.match(
        r'^using\s+("?)(?P<filename>.+?)\1(?:\s*,\s*(?P<options>.*))?$',
        rest,
    )
    if match is None:
        return INVALID_SYNTAX

    path = Path(match.group("filename"))
    if not path.is_absolute():
        path = Path.cwd() / path
    try:
        data = _parse_yaml_subset(path.read_text())
    except (OSError, ValueError):
        return INVALID_SYNTAX

    entries = _flatten_yaml(data)
    state.yaml_entries = {entry.key: entry for entry in entries}
    options = _parse_options(match.group("options") or "")
    prefix = options.get("prefix", "yaml_")

    state.returns.update(
        {
            "filename": path.as_posix(),
            "n_keys": str(len(entries)),
            "max_level": str(max((entry.level for entry in entries), default=0)),
            "yaml_mode": "canonical",
            "cache_hit": "0",
        }
    )
    if "locals" in options:
        state.returns.update(
            {
                f"{prefix}{entry.key}": entry.value
                for entry in entries
                if entry.type != "parent"
            }
        )
    return None


def _yaml_get(rest: str, state: RuntimeState) -> int | None:
    query, options = _split_command_options(rest)
    query = query.strip()
    if not query:
        return INVALID_SYNTAX

    parent, _, key = query.partition(":")
    if key:
        search_key = f"{parent}_{key}"
        result_name = key
    else:
        search_key = parent
        result_name = parent.rsplit("_", maxsplit=1)[-1]

    entry = state.yaml_entries.get(search_key)
    children = _get_yaml_child_attributes(search_key, state)
    state.returns.update(
        {
            "key": key or parent,
            "parent": parent if key else "",
            "found": "1" if entry is not None or children else "0",
            "n_attrs": str(len(children) or int(entry is not None)),
        }
    )
    if children:
        attributes = str(options.get("attributes", "")).split()
        allowed = set(attributes) if attributes else set(children)
        state.returns.update(
            {attr: value for attr, value in children.items() if attr in allowed}
        )
    elif entry is not None:
        state.returns[result_name] = entry.value
    return None


def _get_yaml_child_attributes(
    search_key: str,
    state: RuntimeState,
) -> dict[str, str]:
    prefix = f"{search_key}_"
    attributes: dict[str, str] = {}
    for key, entry in state.yaml_entries.items():
        if not key.startswith(prefix) or entry.type == "parent":
            continue
        attribute = key.removeprefix(prefix)
        if "_" not in attribute:
            attributes[attribute] = entry.value
    return attributes


def _yaml_validate(rest: str, state: RuntimeState) -> int | None:
    _, options = _split_command_options(rest)
    valid = True

    required = str(options.get("required", "")).split()
    for key in required:
        valid = valid and key in state.yaml_entries

    for spec in str(options.get("types", "")).split():
        key, separator, expected_type = spec.partition(":")
        if not separator:
            return INVALID_SYNTAX
        entry = state.yaml_entries.get(key)
        valid = valid and entry is not None and entry.type == expected_type

    state.returns["valid"] = "1" if valid else "0"
    return None if valid else INVALID_SYNTAX


def _parse_yaml_subset(text: str) -> dict[str, Any]:
    if re.search(r"(^|\s)(---|\{|\}|\[[^\]]*\]|&\w+|\*\w+)", text):
        msg = "Unsupported YAML syntax."
        raise ValueError(msg)

    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent % 2:
            msg = "Only two-space indentation is supported."
            raise ValueError(msg)

        stripped = raw_line.strip()
        if stripped.startswith("- "):
            msg = "Top-level list items are not supported."
            raise ValueError(msg)
        key, separator, value = stripped.partition(":")
        if not separator or not key or " " in key:
            msg = "Invalid YAML mapping key."
            raise ValueError(msg)

        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value.strip() == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_yaml_scalar(value.strip())

    return root


def _parse_yaml_scalar(value: str) -> str | int | float | bool | None:
    value = value.strip("\"'")
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.lower() in {"null", "~"}:
        return None
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def _flatten_yaml(data: dict[str, Any]) -> list[YamlEntry]:
    entries: list[YamlEntry] = []

    def recurse(value: Any, prefix: str, level: int, parent: str) -> None:
        if isinstance(value, dict):
            if prefix:
                entries.append(YamlEntry(prefix, "", level, parent, "parent"))
            for key, child in value.items():
                child_key = f"{prefix}_{key}" if prefix else key
                recurse(child, child_key, level + 1, prefix)
            return

        entries.append(
            YamlEntry(
                key=prefix,
                value=_format_yaml_value(value),
                level=level,
                parent=parent,
                type=_yaml_value_type(value),
            )
        )

    recurse(data, "", 0, "")
    return entries


def _format_yaml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)


def _yaml_value_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int | float):
        return "numeric"
    if value is None:
        return "null"
    return "string"


def _split_command_options(rest: str) -> tuple[str, dict[str, str | bool]]:
    command, separator, options = rest.partition(",")
    return command.strip(), _parse_options(options if separator else "")


def _parse_options(options: str) -> dict[str, str | bool]:
    parsed: dict[str, str | bool] = {}
    for option in _split_options(options):
        if match := re.match(r"(?P<name>\w+)\((?P<value>.*)\)$", option):
            parsed[_normalize_option_name(match.group("name"))] = match.group("value")
        elif option:
            parsed[_normalize_option_name(option)] = True
    return parsed


def _split_options(options: str) -> list[str]:
    return re.findall(r"\w+\([^)]*\)|\w+", options)


def _normalize_option_name(name: str) -> str:
    return {"l": "locals", "s": "scalars", "q": "quiet"}.get(name, name)


def _expand_macros(line: str, state: RuntimeState) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if r_match := re.fullmatch(r"r\(([^)]+)\)", name):
            return state.returns.get(r_match.group(1), "")
        return state.macros.get(name, "")

    return re.sub(r"`([^']+)'", replace, line)


def _parse_save_target(rest: str) -> str:
    target = rest.split(",", maxsplit=1)[0].strip()
    return target.strip("\"'")


if __name__ == "__main__":
    raise SystemExit(main())
