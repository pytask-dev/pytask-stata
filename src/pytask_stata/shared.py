"""Shared functions and variables."""
import sys


if sys.platform == "darwin":
    STATA_COMMANDS = [
        "Stata64MP",
        "StataMP",
        "Stata64SE",
        "StataSE",
        "Stata64",
        "Stata",
    ]
elif sys.platform == "linux":
    STATA_COMMANDS = ["stata-mp", "stata-se", "stata"]
elif sys.platform == "win32":
    STATA_COMMANDS = [
        "StataMP-64",
        "StataMP-ia",
        "StataMP",
        "StataSE-64",
        "StataSE-ia",
        "StataSE",
        "Stata-64",
        "Stata-ia",
        "Stata",
        "WMPSTATA",
        "WSESTATA",
        "WSTATA",
    ]
else:
    STATA_COMMANDS = []


def convert_task_id_to_name_of_log_file(id_):
    """Convert task to id to name of log file.

    If one passes the complete task id as the log file name, Stata would remove parent
    directories and cut the string at the double colons for parametrized task. Here is
    an example:

    .. code-block:: none

        C:/task_dummy.py::task_dummy[arg1] -> task_dummy.log

    This function creates a new id starting from the task module and by replacing dots
    and double colons with underscores.

    Example
    -------
    >>> convert_task_id_to_name_of_log_file("C:/task_dummy.py::task_dummy[arg1]")
    'task_dummy_py_task_dummy[arg1]'

    """
    id_without_parent_directories = id_.rsplit("/")[-1]
    converted_id = id_without_parent_directories.replace(".", "_").replace("::", "_")
    return converted_id


def get_node_from_dictionary(obj, key, fallback=0):
    if isinstance(obj, dict):
        obj = obj.get(key) or obj.get(fallback)
    return obj
