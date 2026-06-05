from __future__ import annotations

import re
import sys
from pathlib import Path

INVALID_SYNTAX = 198
UNKNOWN_COMMAND = 199
MINIMUM_ARGUMENTS = 4


def main() -> int:
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
    macros: dict[str, str] = {}

    for raw_line in script.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("*"):
            continue

        line = _expand_local_macros(line, macros)
        lines.append(f". {line}")
        error_code = _execute_line(line, macros, options)
        if error_code is not None:
            return lines, error_code

    return lines, None


def _execute_line(line: str, macros: dict[str, str], options: list[str]) -> int | None:
    command, _, rest = line.partition(" ")
    command = command.lower()
    rest = rest.strip()

    if command == "args":
        macros.update(dict(zip(rest.split(), options, strict=False)))
    elif command == "sysuse":
        return None
    elif command == "save":
        return _save_dataset(rest)
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


def _expand_local_macros(line: str, macros: dict[str, str]) -> str:
    return re.sub(r"`([^']+)'", lambda match: macros.get(match.group(1), ""), line)


def _parse_save_target(rest: str) -> str:
    target = rest.split(",", maxsplit=1)[0].strip()
    return target.strip("\"'")


if __name__ == "__main__":
    raise SystemExit(main())
