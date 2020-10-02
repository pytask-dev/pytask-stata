import pytest
from pytask import main
from pytask_stata.config import _nonnegative_nonzero_integer


@pytest.mark.end_to_end
def test_marker_is_configured(tmp_path):
    session = main({"paths": tmp_path})

    assert "stata" in session.config
    assert "stata" in session.config["markers"]


@pytest.mark.unit
@pytest.mark.parametrize("x, expected", [(None, None), (1, 1), ("1", 1), (1.5, 1)])
def test_nonnegative_nonzero_integer(x, expected):
    assert _nonnegative_nonzero_integer(x) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "x, expectation",
    [
        (
            -1,
            pytest.raises(ValueError, match="'stata_check_log_lines' must be greater"),
        ),
        (
            "-1",
            pytest.raises(ValueError, match="'stata_check_log_lines' must be greater"),
        ),
        (0, pytest.raises(ValueError, match="'stata_check_log_lines' must be greater")),
        (
            "0",
            pytest.raises(ValueError, match="'stata_check_log_lines' must be greater"),
        ),
        (
            "1.5",
            pytest.raises(ValueError, match="'stata_check_log_lines' must be a"),
        ),
    ],
)
def test_nonnegative_nonzero_integer_raises_error(x, expectation):
    with expectation:
        _nonnegative_nonzero_integer(x)
