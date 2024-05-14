"""Parametrize tasks."""

from __future__ import annotations

from typing import Any
from typing import Callable

import pytask
from _pytask.config import hookimpl


@hookimpl
def pytask_parametrize_kwarg_to_marker(obj: Callable[..., Any], kwargs: Any) -> None:
    """Attach parametrized stata arguments to the function with a marker."""
    if callable(obj) and "stata" in kwargs:
        pytask.mark.stata(**kwargs.pop("stata"))(obj)
