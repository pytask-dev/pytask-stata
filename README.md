# pytask-stata

[![PyPI](https://img.shields.io/pypi/v/pytask-stata?color=blue)](https://pypi.org/project/pytask-stata)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytask-stata)](https://pypi.org/project/pytask-stata)
[![image](https://img.shields.io/conda/vn/conda-forge/pytask-stata.svg)](https://anaconda.org/conda-forge/pytask-stata)
[![image](https://img.shields.io/conda/pn/conda-forge/pytask-stata.svg)](https://anaconda.org/conda-forge/pytask-stata)
[![PyPI - License](https://img.shields.io/pypi/l/pytask-stata)](https://pypi.org/project/pytask-stata)
[![image](https://img.shields.io/github/actions/workflow/status/pytask-dev/pytask-stata/main.yml?branch=main)](https://github.com/pytask-dev/pytask-stata/actions?query=branch%3Amain)
[![image](https://codecov.io/gh/pytask-dev/pytask-stata/branch/main/graph/badge.svg)](https://codecov.io/gh/pytask-dev/pytask-stata)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/pytask-dev/pytask-stata/main.svg)](https://results.pre-commit.ci/latest/github/pytask-dev/pytask-stata/main)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

______________________________________________________________________

Run Stata's do-files with pytask.

## Installation

pytask-stata is available on [PyPI](https://pypi.org/project/pytask-stata) and
[Anaconda.org](https://anaconda.org/conda-forge/pytask-stata). Install it with

```console
$ uv add pytask-stata

# or

$ pixi add pytask-stata
```

You also need to have Stata installed on your system and have the executable on your
system's PATH. If you do not know how to do it, [here](https://superuser.com/a/284351)
is an explanation.

## Usage

Similarly to normal task functions which execute Python code, you define tasks to
execute scripts written in Stata with Python functions. The difference is that the
function body does not contain any logic, but the decorator tells pytask how to handle
the task.

Here is an example where you want to run `script.do`.

```python
from pathlib import Path

from pytask import mark


@mark.stata(script=Path("script.do"))
def task_run_do_file(produces: Path = Path("auto.dta")):
    pass
```

When executing a do-file, the current working directory changes to the directory where
the task module is located. This allows you, for example, to reference data sets with a
relative path from the task module.

### Dependencies and Products

Dependencies and products can be added as with a normal pytask task using the task
function signature as explained in this
[tutorial](https://pytask-dev.readthedocs.io/en/stable/tutorials/defining_dependencies_products.html).

### Accessing dependencies and products in the script

Dependencies and products registered in the task function signature are used by pytask
to order tasks and track whether they are up-to-date. If `options` is not used,
pytask-stata writes all dependencies and products from the task function signature to a
YAML file and passes the path to this file as the first command line argument to the
do-file.

#### Command Line Arguments

Use the `options` argument of the decorator to keep the legacy interface and pass paths
or other values as command line arguments to your Stata executable.

For example, pass the path of the product with

```python
from pathlib import Path

from pytask import mark


@mark.stata(script=Path("script.do"), options=Path("auto.dta"))
def task_run_do_file(produces: Path = Path("auto.dta")):
    pass
```

And in your `script.do`, you can intercept the value with

```do
* Intercept command line argument and save to macro named 'produces'.
args produces

sysuse auto, clear
save "`produces'"
```

The relative path inside the do-file works only because pytask-stata switches the
current working directory to the directory of the task module before the task is
executed.

To make the task independent from the current working directory, pass the full path as
an command line argument. Here is an example.

```python
# Absolute path to the build directory.
from pathlib import Path

from pytask import mark

from src.config import BLD


@mark.stata(script=Path("script.do"), options=BLD / "auto.dta")
def task_run_do_file(produces: Path = BLD / "auto.dta"):
    pass
```

#### YAML Configuration Files

By default, pytask-stata serializes all task keyword arguments and passes the path to
the generated YAML file as the first argument to the do-file. To read the file inside
Stata, install the user-written `yaml` package.

```stata
ssc install yaml
```

Then read the configuration file in the Stata task.

```python
@mark.stata(script=Path("script.do"))
def task_run_do_file(produces: Path = Path("auto.dta")):
    pass
```

```do
args config
yaml read using "`config'", locals replace

sysuse auto, clear
save "`r(yaml_produces)'"
```

Do not combine both interfaces. If `options` is supplied, pytask-stata assumes the
do-file receives all required values through command line arguments and does not create
a YAML configuration file.

### Repeating tasks with different scripts or inputs

You can also parametrize the execution of scripts, meaning executing multiple do-files
as well as passing different command line arguments to the same do-file.

The following task executes two do-files which produce different outputs.

```python
from pathlib import Path

from pytask import mark
from pytask import task

for i in range(2):

    @task
    @mark.stata(script=Path(f"script_{i}.do"), options=f"{i}.dta")
    def task_execute_do_file(produces: Path = Path(f"{i}.dta")):
        pass
```

## Configuration

pytask-stata can be configured with the following options.

*`stata_keep_log`*

Use this option to keep the `.log` files which are produced for every task. This option
is useful to debug Stata tasks. Set the option via the configuration file with

```toml
[tool.pytask.ini_options]
stata_keep_log = true
```

The option is also available in the command line interface via the `--stata-keep-log`
flag.

*`stata_check_log_lines`*

Use this option to vary the number of lines in the log file which are checked for error
codes. It also controls the number of lines displayed on errors. Use any integer greater
than zero. Here is the entry in the configuration file

```toml
[tool.pytask.ini_options]
stata_check_log_lines = 10
```

and here via the command line interface

```console
$ pytask build --stata-check-log-lines 10
```

## Changes

Consult the [release notes](CHANGELOG.md) to find out about what is new.
