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
def stata_runtime(tmp_path_factory):
    """Use mock Stata on CI and require a real Stata executable locally."""
    if os.environ.get("CI"):
        bin_path = tmp_path_factory.mktemp("mock_stata_bin")
        mock_stata_path = Path(__file__).with_name("mock_stata.py")
        original_path = os.environ["PATH"]
        original_pathext = os.environ.get("PATHEXT")

        if sys.platform == "win32":
            for executable in STATA_COMMANDS:
                shim = bin_path / f"{executable}.cmd"
                shim.write_text(
                    f'@echo off\n"{sys.executable}" "{mock_stata_path}" %*\n'
                )
            os.environ["PATHEXT"] = ".COM;.EXE;.BAT;.CMD"
        else:
            for executable in STATA_COMMANDS:
                shim = bin_path / executable
                shim.write_text(
                    f'#!/bin/sh\nexec "{sys.executable}" "{mock_stata_path}" "$@"\n'
                )
                shim.chmod(0o755)

        os.environ["PATH"] = f"{bin_path}{os.pathsep}{original_path}"
        mock_executable = shutil.which(STATA_COMMANDS[0])

        warnings.warn(
            "Using mock Stata runtime because CI is set: "
            f"{mock_executable} -> {mock_stata_path}.",
            stacklevel=1,
        )
        yield

        os.environ["PATH"] = original_path
        if original_pathext is None:
            os.environ.pop("PATHEXT", None)
        else:
            os.environ["PATHEXT"] = original_pathext
        return

    executable = next(
        (executable for executable in STATA_COMMANDS if shutil.which(executable)),
        None,
    )
    if executable is None:
        msg = (
            "Stata-dependent tests require a real Stata executable on PATH when CI is "
            "not set. Set CI=1 to run them against tests/mock_stata.py."
        )
        pytest.fail(msg)

    yield


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
