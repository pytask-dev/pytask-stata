"""Configure pytask."""

from __future__ import annotations

import shutil
import sys
from typing import Any

from pytask import hookimpl

from pytask_stata.shared import STATA_COMMANDS


@hookimpl
def pytask_parse_config(config: dict[str, Any]) -> None:
    """Register the r marker."""
    config["markers"]["stata"] = "Tasks which are executed with Stata."
    config["platform"] = sys.platform

    if not config.get("stata"):
        config["stata"] = next(
            (executable for executable in STATA_COMMANDS if shutil.which(executable)),
            None,
        )
