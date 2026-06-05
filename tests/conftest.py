from __future__ import annotations

import os
import shutil
import sys
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from click.testing import CliRunner
from pytask import storage

from pytask_stata.config import STATA_COMMANDS

if TYPE_CHECKING:
    from collections.abc import Callable

needs_stata = pytest.mark.usefixtures("stata_runtime")


@pytest.fixture(scope="session")
def stata_runtime():
    """Use mock Stata on CI and require a real Stata executable locally."""
    executable_path = _find_stata_executable()
    if os.environ.get("CI"):
        if executable_path is None:
            msg = (
                "CI requires the stata-mock package to be installed so one of "
                f"{STATA_COMMANDS} is available on PATH."
            )
            pytest.fail(msg)
        warnings.warn(
            f"Using mock Stata runtime because CI is set: {executable_path}.",
            stacklevel=1,
        )
        yield
        return

    if executable_path is None or _is_mock_stata_executable(executable_path):
        msg = (
            "Stata-dependent tests require a real Stata executable on PATH when CI is "
            "not set. Run the CI test recipe to use the stata-mock package."
        )
        pytest.fail(msg)

    yield


def _is_mock_stata_executable(executable_path: str) -> bool:
    try:
        Path(executable_path).resolve().relative_to(Path(sys.prefix).resolve())
    except ValueError:
        return False
    else:
        return True


def _find_stata_executable() -> str | None:
    return next(
        (path for executable in STATA_COMMANDS if (path := shutil.which(executable))),
        None,
    )


class SysPathsSnapshot:
    """A snapshot for sys.path."""

    def __init__(self) -> None:
        self.__saved = sys.path.copy(), sys.meta_path.copy()

    def restore(self) -> None:
        sys.path[:], sys.meta_path[:] = self.__saved


class SysModulesSnapshot:
    """A snapshot for sys.modules."""

    def __init__(self, preserve: Callable[[str], bool] | None = None) -> None:
        self.__preserve = preserve
        self.__saved = sys.modules.copy()

    def restore(self) -> None:
        if self.__preserve:
            self.__saved.update(
                (k, m) for k, m in sys.modules.items() if self.__preserve(k)
            )
        sys.modules.clear()
        sys.modules.update(self.__saved)


@contextmanager
def restore_sys_path_and_module_after_test_execution():
    sys_path_snapshot = SysPathsSnapshot()
    sys_modules_snapshot = SysModulesSnapshot()
    yield
    sys_modules_snapshot.restore()
    sys_path_snapshot.restore()


@pytest.fixture(autouse=True)
def _restore_sys_path_and_module_after_test_execution():
    """Restore sys.path and sys.modules after every test execution.

    This fixture became necessary because most task modules in the tests are named
    `task_example`. Since the change in #424, the same module is not reimported which
    solves errors with parallelization. At the same time, modules with the same name in
    the tests are overshadowing another and letting tests fail.

    The changes to `sys.path` might not be necessary to restore, but we do it anyways.

    """
    with restore_sys_path_and_module_after_test_execution():
        yield


class CustomCliRunner(CliRunner):
    def invoke(self, *args, **kwargs):
        """Restore sys.path and sys.modules after an invocation."""
        storage.create()
        with restore_sys_path_and_module_after_test_execution():
            return super().invoke(*args, **kwargs)


@pytest.fixture
def runner():
    return CustomCliRunner()
