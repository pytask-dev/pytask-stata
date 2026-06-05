from __future__ import annotations

import textwrap

from pytask import ExitCode
from pytask import cli

from tests.conftest import needs_stata


@needs_stata
def test_parametrized_execution_of_do_file_w_loop(runner, tmp_path):
    source = """
    import pytask
    from pathlib import Path
    from pytask import task

    for i in range (1, 3):

        @task
        @pytask.mark.stata(script=f"script_{i}.do")
        def task_execute_do_file(produces=Path(f"{i}.dta")):
            pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    for i in range(1, 3):
        do_file = f"""
        sysuse auto, clear
        save {i}
        """
        tmp_path.joinpath(f"script_{i}.do").write_text(textwrap.dedent(do_file))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("1.dta").exists()
    assert tmp_path.joinpath("2.dta").exists()


@needs_stata
def test_parametrize_command_line_options_w_loop(runner, tmp_path):
    task_source = """
    import pytask
    from pathlib import Path
    from pytask import task

    for i in range (1, 3):

        @task
        @pytask.mark.stata(script="script.do", options=f"output_{i}")
        def task_execute_do_file(produces=Path(f"output_{i}.dta")):
            pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(task_source))

    latex_source = """
    sysuse auto, clear
    args produces
    save "`produces'"
    """
    tmp_path.joinpath("script.do").write_text(textwrap.dedent(latex_source))

    result = runner.invoke(cli, [tmp_path.as_posix(), "--stata-keep-log"])

    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("output_1.dta").exists()
    assert tmp_path.joinpath("output_2.dta").exists()

    assert list(tmp_path.glob("*.log"))
