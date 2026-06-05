from __future__ import annotations

import textwrap
from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path

import pytest
from pytask import ExitCode
from pytask import Mark
from pytask import Session
from pytask import Task
from pytask import build
from pytask import cli

from pytask_stata.config import STATA_COMMANDS
from pytask_stata.execute import pytask_execute_task_setup
from tests.conftest import needs_stata


def _assert_log_exists(path: Path) -> None:
    assert list(path.glob("*.log"))


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
        function=lambda: None,
        markers=[Mark("stata", (), {})],
    )

    session = Session(config={"stata": stata, "platform": platform})

    with expectation:
        pytask_execute_task_setup(session, task)


@needs_stata
def test_run_do_file(runner, tmp_path):
    task_source = """
    import pytask
    from pathlib import Path

    @pytask.mark.stata(script="script.do")
    def task_run_do_file(produces=Path("auto.dta")):
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

    _assert_log_exists(tmp_path)


@needs_stata
def test_run_do_file_w_task_decorator(runner, tmp_path):
    task_source = """
    import pytask
    from pathlib import Path
    from pytask import task

    @task
    @pytask.mark.stata(script="script.do")
    def run_do_file(produces=Path("auto.dta")):
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

    _assert_log_exists(tmp_path)


def test_raise_error_if_stata_is_not_found(tmp_path, monkeypatch):
    task_source = """
    from pytask import mark, task

    @task(kwargs={"produces": "out.dta"})
    @mark.stata(script="script.do")
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

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.FAILED
    exc_info = session.execution_reports[0].exc_info
    assert exc_info is not None
    assert isinstance(exc_info[1], RuntimeError)


@needs_stata
def test_run_do_file_w_wrong_cmd_option(runner, tmp_path):
    """Apparently, Stata simply discards wrong cmd options."""
    task_source = """
    import pytask
    from pathlib import Path

    @pytask.mark.stata(script="script.do", options="--wrong-flag")
    def task_run_do_file(produces=Path("out.dta")):
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
    assert tmp_path.joinpath("out.dta").exists()


@needs_stata
def test_run_do_file_by_passing_path(runner, tmp_path):
    """Replicates example under "Command Line Arguments" in Readme."""
    task_source = """
    import pytask
    from pathlib import Path

    @pytask.mark.stata(script="script.do", options=Path(__file__).parent / "auto.dta")
    def task_run_do_file(produces=Path("auto.dta")):
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
def test_run_do_file_fails_with_stata_error(runner, tmp_path):
    task_source = """
    import pytask
    from pathlib import Path

    @pytask.mark.stata(script="script.do")
    def task_run_do_file(produces=Path("out.dta")):
        pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(task_source))

    do_file = """
    error 601
    """
    tmp_path.joinpath("script.do").write_text(textwrap.dedent(do_file))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.FAILED
    assert "r(601)" in result.output


@needs_stata
def test_run_do_file_fails_with_multiple_marks(runner, tmp_path):
    task_source = """
    import pytask
    from pathlib import Path

    @pytask.mark.stata(script="script.do")
    @pytask.mark.stata(script="script.do")
    def task_run_do_file(produces=Path("auto.dta")):
        pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(task_source))
    tmp_path.joinpath("script.do").touch()

    result = runner.invoke(cli, [tmp_path.as_posix(), "--stata-keep-log"])

    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert "has multiple @pytask.mark.stata marks" in result.output


@needs_stata
def test_with_task_without_path(runner, tmp_path):
    task_source = """
    import pytask
    from pathlib import Path
    from pytask import task

    task_example = pytask.mark.stata(script="script.do")(
        task(kwargs={"produces": Path("auto.dta")})(lambda produces: None)
    )
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

    _assert_log_exists(tmp_path)
