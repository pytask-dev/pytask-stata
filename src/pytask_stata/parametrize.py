"""Parametrize tasks."""
from __future__ import annotations

import pytask
from pytask import hookimpl


@hookimpl
def pytask_parametrize_kwarg_to_marker(obj, kwargs):
    """Attach parametrized stata arguments to the function with a marker."""
    if callable(obj):
        if "stata" in kwargs:
            pytask.mark.stata(**kwargs.pop("stata"))(obj)
