import shutil

import pytest
from pytask_stata.config import STATA_COMMANDS


needs_stata = pytest.mark.skipif(
    next(
        (executable for executable in STATA_COMMANDS if shutil.which(executable)), None
    )
    is None,
    reason="Stata needs to be installed.",
)
