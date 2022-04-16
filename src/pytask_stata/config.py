"""Configure pytask."""
from __future__ import annotations

import shutil
import sys
from typing import Any
from typing import Callable

from pytask import hookimpl
from pytask_stata.shared import STATA_COMMANDS


@hookimpl
def pytask_parse_config(
    config: dict[str, Any],
    config_from_cli: dict[str, Any],
    config_from_file: dict[str, Any],
) -> None:
    """Register the r marker."""
    config["markers"]["stata"] = "Tasks which are executed with Stata."
    config["platform"] = sys.platform

    if config_from_file.get("stata"):
        config["stata"] = config_from_file["stata"]
    else:
        config["stata"] = next(
            (executable for executable in STATA_COMMANDS if shutil.which(executable)),
            None,
        )

    config["stata_keep_log"] = _get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="stata_keep_log",
        callback=_convert_truthy_or_falsy_to_bool,
        default=False,
    )

    config["stata_check_log_lines"] = _get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="stata_check_log_lines",
        callback=_nonnegative_nonzero_integer,
        default=10,
    )


def _nonnegative_nonzero_integer(x: Any) -> int:
    """Check for nonnegative and nonzero integer."""
    if x is not None:
        try:
            x = int(x)
        except ValueError:
            raise ValueError(
                "'stata_check_log_lines' must be a nonzero and nonnegative integer, "
                f"but it is '{x}'."
            )

        if x <= 0:
            raise ValueError("'stata_check_log_lines' must be greater than zero.")

    return x


def _get_first_non_none_value(
    *configs: dict[str, Any],
    key: str,
    default: Any | None = None,
    callback: Callable[..., Any] | None = None,
) -> Any:
    """Get the first non-None value for a key from a list of dictionaries.

    This function allows to prioritize information from many configurations by changing
    the order of the inputs while also providing a default.

    Examples
    --------
    >>> _get_first_non_none_value({"a": None}, {"a": 1}, key="a")
    1
    >>> _get_first_non_none_value({"a": None}, {"a": None}, key="a", default="default")
    'default'
    >>> _get_first_non_none_value({}, {}, key="a", default="default")
    'default'
    >>> _get_first_non_none_value({"a": None}, {"a": "b"}, key="a")
    'b'

    """
    callback = (lambda x: x) if callback is None else callback  # noqa: E731
    processed_values = (callback(config.get(key)) for config in configs)
    return next((value for value in processed_values if value is not None), default)


def _convert_truthy_or_falsy_to_bool(x: bool | str | None) -> bool:
    """Convert truthy or falsy value in .ini to Python boolean."""
    if x in [True, "True", "true", "1"]:
        out = True
    elif x in [False, "False", "false", "0"]:
        out = False
    elif x in [None, "None", "none"]:
        out = None
    else:
        raise ValueError(
            f"Input {x!r} is neither truthy (True, true, 1) or falsy (False, false, 0)."
        )
    return out
