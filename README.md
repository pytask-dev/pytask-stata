# pytask-stata

[![PyPI](https://img.shields.io/pypi/v/pytask-stata?color=blue)](https://pypi.org/project/pytask-stata)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytask-stata)](https://pypi.org/project/pytask-stata)
[![image](https://img.shields.io/conda/vn/conda-forge/pytask-stata.svg)](https://anaconda.org/conda-forge/pytask-stata)
[![image](https://img.shields.io/conda/pn/conda-forge/pytask-stata.svg)](https://anaconda.org/conda-forge/pytask-stata)
[![PyPI - License](https://img.shields.io/pypi/l/pytask-stata)](https://pypi.org/project/pytask-stata)
[![image](https://img.shields.io/github/actions/workflow/status/pytask-dev/pytask-stata/main.yml?branch=main)](https://github.com/pytask-dev/pytask-stata/actions?query=branch%3Amain)
[![image](https://codecov.io/gh/pytask-dev/pytask-stata/branch/main/graph/badge.svg)](https://codecov.io/gh/pytask-dev/pytask-stata)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/pytask-dev/pytask-stata/main.svg)](https://results.pre-commit.ci/latest/github/pytask-dev/pytask-stata/main)
[![image](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

______________________________________________________________________

Run Stata's do-files with pytask.

## Installation

pytask-stata is available on [PyPI](https://pypi.org/project/pytask-stata) and
[Anaconda.org](https://anaconda.org/conda-forge/pytask-stata). Install it with

```console
$ pip install pytask-stata

# or

$ conda install -c conda-forge pytask-stata
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
import pytask


@pytask.mark.stata(script="script.do")
@pytask.mark.produces("auto.dta")
def task_run_do_file():
    pass
```

When executing a do-file, the current working directory changes to the directory where
the script is located. This allows you, for example, to reference every data set you
want to read with a relative path from the script.

### Dependencies and Products

Dependencies and products can be added as with a normal pytask task using the
`@pytask.mark.depends_on` and `@pytask.mark.produces` decorators. which is explained in
this
[tutorial](https://pytask-dev.readthedocs.io/en/stable/tutorials/defining_dependencies_products.html).

### Accessing dependencies and products in the script

The decorator can be used to pass command line arguments to your Stata executable. For
example, pass the path of the product with

```python
@pytask.mark.stata(script="script.do", options="auto.dta")
@pytask.mark.produces("auto.dta")
def task_run_do_file():
    pass
```

And in your `script.do`, you can intercept the value with

```do
* Intercept command line argument and save to macro named 'produces'.
args produces

sysuse auto, clear
save "`produces'"
```

The relative path inside the do-file works only because the pytask-stata switches the
current working directory to the directory of the do-file before the task is executed.

To make the task independent from the current working directory, pass the full path as
an command line argument. Here is an example.

```python
# Absolute path to the build directory.
from src.config import BLD


@pytask.mark.stata(script="script.do", options=BLD / "auto.dta")
@pytask.mark.produces(BLD / "auto.dta")
def task_run_do_file():
    pass
```

### Repeating tasks with different scripts or inputs

You can also parametrize the execution of scripts, meaning executing multiple do-files
as well as passing different command line arguments to the same do-file.

The following task executes two do-files which produce different outputs.

```python
for i in range(2):

    @pytask.mark.task
    @pytask.mark.stata(script=f"script_{i}.do", options=f"{i}.dta")
    @pytask.mark.produces(f"{i}.dta")
    def task_execute_do_file():
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

Consult the [release notes](CHANGES.md) to find out about what is new.
