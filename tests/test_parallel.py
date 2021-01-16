"""Contains test which ensure that the plugin works with pytask-parallel."""
import textwrap
import time

import pytest
from conftest import needs_stata
from pytask import cli

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
@pytest.mark.end_to_end
def test_parallel_parametrization_over_source_files(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.stata
    @pytask.mark.parametrize(
        "depends_on, produces", [("script_1.do", "1.dta"), ("script_2.do", "2.dta")]
    )
    def task_execute_do_file():
        pass
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    do_file = """
    sleep 2000
    sysuse auto, clear
    save 1
    """
    tmp_path.joinpath("script_1.do").write_text(textwrap.dedent(do_file))

    do_file = """
    sleep 2000
    sysuse auto, clear
    save 2
    """
    tmp_path.joinpath("script_2.do").write_text(textwrap.dedent(do_file))

    start = time.time()
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == 0
    duration_normal = time.time() - start

    for name in ["1.dta", "2.dta"]:
        tmp_path.joinpath(name).unlink()

    start = time.time()
    result = runner.invoke(cli, [tmp_path.as_posix(), "-n", 2])
    assert result.exit_code == 0
    duration_parallel = time.time() - start

    assert duration_parallel < duration_normal


@needs_stata
@pytest.mark.end_to_end
def test_parallel_parametrization_over_source_file(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.depends_on("script.do")
    @pytask.mark.parametrize(
        "produces, stata",
        [("output_1.dta", ("output_1",)), ("output_2.dta", ("output_2",))],
    )
    def task_execute_do_file():
        pass
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    do_file = """
    sleep 2000
    sysuse auto, clear
    args produces
    save "`produces'"
    """
    tmp_path.joinpath("script.do").write_text(textwrap.dedent(do_file))

    start = time.time()
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == 0
    duration_normal = time.time() - start

    for name in ["output_1.dta", "output_2.dta"]:
        tmp_path.joinpath(name).unlink()

    start = time.time()
    result = runner.invoke(cli, [tmp_path.as_posix(), "-n", 2])
    assert result.exit_code == 0
    duration_parallel = time.time() - start

    assert duration_parallel < duration_normal
