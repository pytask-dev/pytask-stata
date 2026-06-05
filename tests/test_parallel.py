"""Contains test which ensure that the plugin works with pytask-parallel."""

from __future__ import annotations

import textwrap

import pytest
from pytask import ExitCode
from pytask import cli

from tests.conftest import needs_stata

try:
    import pytask_parallel  # noqa: F401
except ImportError:
    _IS_PYTASK_PARALLEL_INSTALLED = False
else:
    _IS_PYTASK_PARALLEL_INSTALLED = True


pytestmark = pytest.mark.skipif(
    not _IS_PYTASK_PARALLEL_INSTALLED, reason="Tests require pytask-parallel."
)


@needs_stata
def test_parallel_parametrization_over_source_files_w_loop(runner, tmp_path):
    source = """
    import pytask
    from pathlib import Path
    from pytask import task

    for i in range (1, 3):

        @task(id=str(i))
        @pytask.mark.stata(script=f"script_{i}.do")
        def task_execute_do_file(produces=Path(f"{i}.dta")):
            pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    do_file = """
    sysuse auto, clear
    save 1
    """
    tmp_path.joinpath("script_1.do").write_text(textwrap.dedent(do_file))

    do_file = """
    sysuse auto, clear
    save 2
    """
    tmp_path.joinpath("script_2.do").write_text(textwrap.dedent(do_file))

    result = runner.invoke(cli, [tmp_path.as_posix(), "-n", 2])
    assert result.exit_code == ExitCode.OK


@needs_stata
def test_parallel_parametrization_over_source_file_w_loop(runner, tmp_path):
    source = """
    import pytask
    from pathlib import Path
    from pytask import task

    for i in range (1, 3):

        @task(id=str(i))
        @pytask.mark.stata(script="script.do", options=f"output_{i}")
        def task_execute_do_file(produces=Path(f"output_{i}.dta")):
            pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    do_file = """
    sysuse auto, clear
    args produces
    save "`produces'"
    """
    tmp_path.joinpath("script.do").write_text(textwrap.dedent(do_file))

    result = runner.invoke(cli, [tmp_path.as_posix(), "-n", 2])
    assert result.exit_code == ExitCode.OK
