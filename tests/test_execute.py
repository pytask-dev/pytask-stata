import os
import sys
import textwrap
from contextlib import ExitStack as does_not_raise  # noqa: N813

import pytest
from _pytask.mark import Mark
from conftest import needs_stata
from pytask import main
from pytask_stata.config import STATA_COMMANDS
from pytask_stata.execute import pytask_execute_task_setup


class DummyClass:
    pass


@pytest.mark.unit
@pytest.mark.parametrize(
    "stata, expectation",
    [(executable, does_not_raise()) for executable in STATA_COMMANDS]
    + [(None, pytest.raises(RuntimeError, match="Stata is needed"))],
)
@pytest.mark.parametrize("platform", ["win32", "linux", "darwin"])
def test_pytask_execute_task_setup_raise_error(stata, platform, expectation):
    """Make sure that the task setup raises errors."""
    # Act like r is installed since we do not test this.
    task = DummyClass()
    task.markers = [Mark("stata", (), {})]

    session = DummyClass()
    session.config = {"stata": stata, "platform": platform}

    with expectation:
        pytask_execute_task_setup(session, task)


@needs_stata
@pytest.mark.end_to_end
def test_run_do_file(tmp_path):
    task_source = """
    import pytask

    @pytask.mark.stata
    @pytask.mark.depends_on("script.do")
    @pytask.mark.produces("auto.dta")
    def task_run_do_file():
        pass
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(task_source))

    do_file = """
    sysuse auto, clear
    save auto
    """
    tmp_path.joinpath("script.do").write_text(textwrap.dedent(do_file))

    os.chdir(tmp_path)
    session = main({"paths": tmp_path, "stata_keep_log": True})

    assert session.exit_code == 0
    assert tmp_path.joinpath("auto.dta").exists()

    if sys.platform == "win32":
        assert tmp_path.joinpath("task_dummy_py_task_run_do_file.log").exists()
    else:
        assert tmp_path.joinpath("script.log").exists()


@pytest.mark.end_to_end
def test_raise_error_if_stata_is_not_found(tmp_path, monkeypatch):
    task_source = """
    import pytask

    @pytask.mark.stata
    @pytask.mark.depends_on("script.do")
    @pytask.mark.produces("out.dta")
    def task_run_do_file():
        pass

    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(task_source))
    tmp_path.joinpath("script.do").write_text(textwrap.dedent("1 + 1"))

    # Hide Stata if available.
    monkeypatch.setattr("pytask_stata.config.shutil.which", lambda x: None)

    session = main({"paths": tmp_path})

    assert session.exit_code == 1
    assert isinstance(session.execution_reports[0].exc_info[1], RuntimeError)


@needs_stata
@pytest.mark.end_to_end
def test_run_do_file_w_wrong_cmd_option(tmp_path):
    """Apparently, Stata simply discards wrong cmd options."""
    task_source = """
    import pytask

    @pytask.mark.stata("--wrong-flag")
    @pytask.mark.depends_on("script.do")
    @pytask.mark.produces("out.dta")
    def task_run_do_file():
        pass

    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(task_source))

    do_file = """
    sysuse auto, clear
    save out
    """
    tmp_path.joinpath("script.do").write_text(textwrap.dedent(do_file))

    os.chdir(tmp_path)
    session = main({"paths": tmp_path})

    assert session.exit_code == 0
