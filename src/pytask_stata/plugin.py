"""Register hook specifications and implementations."""
from __future__ import annotations

from _pytask.config import hookimpl
from pluggy import PluginManager
from pytask_stata import cli
from pytask_stata import collect
from pytask_stata import config
from pytask_stata import execute
from pytask_stata import parametrize


@hookimpl
def pytask_add_hooks(pm: PluginManager) -> None:
    """Register hook implementations."""
    pm.register(cli)
    pm.register(collect)
    pm.register(config)
    pm.register(execute)
    pm.register(parametrize)
