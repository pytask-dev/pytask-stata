"""Configure pytask."""
import shutil
import sys

from _pytask.config import hookimpl
from _pytask.shared import convert_truthy_or_falsy_to_bool
from _pytask.shared import get_first_non_none_value
from pytask_stata.shared import STATA_COMMANDS


@hookimpl
def pytask_parse_config(config, config_from_cli, config_from_file):
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

    config["stata_keep_log"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="stata_keep_log",
        callback=convert_truthy_or_falsy_to_bool,
        default=False,
    )

    config["stata_check_log_lines"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="stata_check_log_lines",
        callback=_nonnegative_nonzero_integer,
        default=10,
    )

    config["stata_source_key"] = config_from_file.get("stata_source_key", "source")


def _nonnegative_nonzero_integer(x):
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
