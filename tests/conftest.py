from __future__ import annotations

import shutil

import pytest
from click.testing import CliRunner
from pytask_stata.config import STATA_COMMANDS

needs_stata = pytest.mark.skipif(
    next(
        (executable for executable in STATA_COMMANDS if shutil.which(executable)), None
    )
    is None,
    reason="Stata needs to be installed.",
)


@pytest.fixture()
def runner():
    return CliRunner()
