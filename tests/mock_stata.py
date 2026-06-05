from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 4 or args[:2] != ["-e", "do"]:
        return 198

    script = Path(args[2]).resolve()
    options = args[3:-1]
    log_arg = args[-1]

    if log_arg == "-":
        log = script.with_suffix(".log")
    else:
        log = Path.cwd() / f"{log_arg.removeprefix('-')}.log"

    lines = [f"running mock Stata for {script.name}"]
    macros: dict[str, str] = {}
    error_code = None

    for raw_line in script.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("*"):
            continue

        line = _expand_local_macros(line, macros)
        lines.append(f". {line}")

        command, _, rest = line.partition(" ")
        command = command.lower()
        rest = rest.strip()

        if command == "args":
            for name, value in zip(rest.split(), options, strict=False):
                macros[name] = value
        elif command == "sysuse":
            continue
        elif command == "save":
            target = _parse_save_target(rest)
            if not target:
                error_code = 198
                break
            path = Path(target)
            if path.suffix == "":
                path = path.with_suffix(".dta")
            if not path.is_absolute():
                path = Path.cwd() / path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("mock Stata dataset\n")
        elif command in {"error", "exit"}:
            error_code = int(rest.split()[0])
            break
        else:
            error_code = 199
            break

    if error_code is not None:
        lines.append(f"r({error_code})")
    else:
        lines.append("end of mock do-file")

    log.write_text("\n".join(lines) + "\n")
    return 0


def _expand_local_macros(line: str, macros: dict[str, str]) -> str:
    return re.sub(r"`([^']+)'", lambda match: macros.get(match.group(1), ""), line)


def _parse_save_target(rest: str) -> str:
    target = rest.split(",", maxsplit=1)[0].strip()
    return target.strip("\"'")


if __name__ == "__main__":
    raise SystemExit(main())
