from __future__ import annotations

import sys
import textwrap

import pytest
from conftest import needs_stata
from pytask import main


@needs_stata
@pytest.mark.end_to_end
def test_parametrized_execution_of_do_file(tmp_path):
    task_source = """
    import pytask

    @pytask.mark.stata
    @pytask.mark.parametrize("depends_on, produces", [
        ("script_1.do", "0.dta"),
        ("script_2.do", "1.dta"),
    ])
    def task_run_do_file():
        pass
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(task_source))

    for name, out in [
        ("script_1.do", "0"),
        ("script_2.do", "1"),
    ]:
        do_file = f"""
        sysuse auto, clear
        save {out}
        """
        tmp_path.joinpath(name).write_text(textwrap.dedent(do_file))

    session = main({"paths": tmp_path})

    assert session.exit_code == 0
    assert tmp_path.joinpath("0.dta").exists()
    assert tmp_path.joinpath("1.dta").exists()


@needs_stata
@pytest.mark.end_to_end
def test_parametrize_command_line_options(tmp_path):
    task_source = """
    import pytask
    from pathlib import Path

    SRC = Path(__file__).parent

    @pytask.mark.depends_on("script.do")
    @pytask.mark.parametrize("produces, stata", [
        (SRC / "0.dta", SRC / "0.dta"), (SRC / "1.dta", SRC / "1.dta"),
    ])
    def task_execute_do_file():
        pass
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(task_source))

    latex_source = """
    sysuse auto, clear
    args produces
    save "`produces'"
    """
    tmp_path.joinpath("script.do").write_text(textwrap.dedent(latex_source))

    session = main({"paths": tmp_path, "stata_keep_log": True})

    assert session.exit_code == 0
    assert tmp_path.joinpath("0.dta").exists()
    assert tmp_path.joinpath("1.dta").exists()

    # Test that log files with different names are produced.
    if sys.platform == "win32":
        assert tmp_path.joinpath(
            "task_dummy_py_task_execute_do_file[produces0-stata0].log"
        ).exists()
        assert tmp_path.joinpath(
            "task_dummy_py_task_execute_do_file[produces1-stata1].log"
        ).exists()
    else:
        assert tmp_path.joinpath("script.log").exists()
