from __future__ import annotations

import sys
import textwrap
from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path

import pytest
from pytask import ExitCode
from pytask import Mark
from pytask import Session
from pytask import Task
from pytask import cli
from pytask import main
from pytask_stata.config import STATA_COMMANDS
from pytask_stata.execute import pytask_execute_task_setup

from tests.conftest import needs_stata


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("stata", "expectation"),
    [(executable, does_not_raise()) for executable in STATA_COMMANDS]
    + [(None, pytest.raises(RuntimeError, match="Stata is needed"))],
)
@pytest.mark.parametrize("platform", ["win32", "linux", "darwin"])
def test_pytask_execute_task_setup_raise_error(stata, platform, expectation):
    """Make sure that the task setup raises errors."""
    # Act like r is installed since we do not test this.
    task = Task(
        base_name="task_example",
        path=Path(),
        function=None,
        markers=[Mark("stata", (), {})],
    )

    session = Session(config={"stata": stata, "platform": platform})

    with expectation:
        pytask_execute_task_setup(session, task)


@needs_stata
@pytest.mark.end_to_end()
def test_run_do_file(runner, tmp_path):
    task_source = """
    import pytask

    @pytask.mark.stata(script="script.do")
    @pytask.mark.produces("auto.dta")
    def task_run_do_file():
        pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(task_source))

    do_file = """
    sysuse auto, clear
    save auto
    """
    tmp_path.joinpath("script.do").write_text(textwrap.dedent(do_file))

    result = runner.invoke(cli, [tmp_path.as_posix(), "--stata-keep-log"])

    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("auto.dta").exists()

    if sys.platform == "win32":
        assert tmp_path.joinpath("task_example_py_task_run_do_file.log").exists()
    else:
        assert tmp_path.joinpath("script.log").exists()


@needs_stata
@pytest.mark.end_to_end()
def test_run_do_file_w_task_decorator(runner, tmp_path):
    task_source = """
    import pytask

    @pytask.mark.task
    @pytask.mark.stata(script="script.do")
    @pytask.mark.produces("auto.dta")
    def run_do_file():
        pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(task_source))

    do_file = """
    sysuse auto, clear
    save auto
    """
    tmp_path.joinpath("script.do").write_text(textwrap.dedent(do_file))

    result = runner.invoke(cli, [tmp_path.as_posix(), "--stata-keep-log"])

    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("auto.dta").exists()

    if sys.platform == "win32":
        assert tmp_path.joinpath("task_example_py_run_do_file.log").exists()
    else:
        assert tmp_path.joinpath("script.log").exists()


@pytest.mark.end_to_end()
def test_raise_error_if_stata_is_not_found(tmp_path, monkeypatch):
    task_source = """
    import pytask

    @pytask.mark.stata(script="script.do")
    @pytask.mark.produces("out.dta")
    def task_run_do_file():
        pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(task_source))
    tmp_path.joinpath("script.do").write_text(textwrap.dedent("1 + 1"))

    # Hide Stata if available.
    monkeypatch.setattr(
        "pytask_stata.config.shutil.which",
        lambda x: None,  # noqa: ARG005
    )

    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.FAILED
    assert isinstance(session.execution_reports[0].exc_info[1], RuntimeError)


@needs_stata
@pytest.mark.end_to_end()
def test_run_do_file_w_wrong_cmd_option(runner, tmp_path):
    """Apparently, Stata simply discards wrong cmd options."""
    task_source = """
    import pytask

    @pytask.mark.stata(script="script.do", options="--wrong-flag")
    @pytask.mark.produces("out.dta")
    def task_run_do_file():
        pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(task_source))

    do_file = """
    sysuse auto, clear
    save out
    """
    tmp_path.joinpath("script.do").write_text(textwrap.dedent(do_file))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK


@needs_stata
@pytest.mark.end_to_end()
def test_run_do_file_by_passing_path(runner, tmp_path):
    """Replicates example under "Command Line Arguments" in Readme."""
    task_source = """
    import pytask
    from pathlib import Path

    @pytask.mark.stata(script="script.do", options=Path(__file__).parent / "auto.dta")
    @pytask.mark.produces("auto.dta")
    def task_run_do_file():
        pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(task_source))

    do_file = """
    args produces
    sysuse auto, clear
    save "`produces'"
    """
    tmp_path.joinpath("script.do").write_text(textwrap.dedent(do_file))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK


@needs_stata
@pytest.mark.end_to_end()
def test_run_do_file_fails_with_multiple_marks(runner, tmp_path):
    task_source = """
    import pytask

    @pytask.mark.stata(script="script.do")
    @pytask.mark.stata(script="script.do")
    @pytask.mark.produces("auto.dta")
    def task_run_do_file():
        pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(task_source))
    tmp_path.joinpath("script.do").touch()

    result = runner.invoke(cli, [tmp_path.as_posix(), "--stata-keep-log"])

    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert "has multiple @pytask.mark.stata marks" in result.output
