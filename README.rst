.. image:: https://img.shields.io/pypi/v/pytask-stata?color=blue
    :alt: PyPI
    :target: https://pypi.org/project/pytask-stata

.. image:: https://img.shields.io/pypi/pyversions/pytask-stata
    :alt: PyPI - Python Version
    :target: https://pypi.org/project/pytask-stata

.. image:: https://anaconda.org/pytask/pytask-stata/badges/version.svg
    :target: https://anaconda.org/pytask/pytask-stata

.. image:: https://anaconda.org/pytask/pytask-stata/badges/platforms.svg
    :target: https://anaconda.org/pytask/pytask-stata

.. image:: https://img.shields.io/pypi/l/pytask-stata
    :alt: PyPI - License

.. image:: https://github.com/pytask-dev/pytask-stata/workflows/Continuous%20Integration%20Workflow/badge.svg?branch=main
    :target: https://github.com/pytask-dev/pytask-stata/actions?query=branch%3Amain

.. image:: https://codecov.io/gh/pytask-dev/pytask-stata/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/pytask-dev/pytask-stata

.. image:: https://results.pre-commit.ci/badge/github/pytask-dev/pytask-stata/main.svg
    :target: https://results.pre-commit.ci/latest/github/pytask-dev/pytask-stata/main
    :alt: pre-commit.ci status

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

------

pytask-stata
============

Run Stata's do-files with pytask.


Installation
------------

pytask-stata is available on `PyPI <https://pypi.org/project/pytask-stata>`_ and
`Anaconda.org <https://anaconda.org/pytask/pytask-stata>`_. Install it with

.. code-block:: console

    $ pip install pytask-stata

    # or

    $ conda config --add channels conda-forge --add channels pytask
    $ conda install pytask-stata

You also need to have Stata installed on your system and have the executable on your
system's PATH. If you do not know how to do it, `here <https://superuser.com/a/284351>`_
is an explanation.


Usage
-----

Similarly to normal task functions which execute Python code, you define tasks to
execute scripts written in Stata with Python functions. The difference is that the
function body does not contain any logic, but the decorator tells pytask how to handle
the task.

Here is an example where you want to run ``script.do``.

.. code-block:: python

    import pytask


    @pytask.mark.stata
    @pytask.mark.depends_on("script.do")
    @pytask.mark.produces("auto.dta")
    def task_run_do_file():
        pass

When executing a do-file, the current working directory changes to the directory of the
script which is executed.


Multiple dependencies and products
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

What happens if a task has more dependencies? Using a list, the do-file which should be
executed must be found in the first position of the list.

.. code-block:: python

    @pytask.mark.stata
    @pytask.mark.depends_on(["script.do", "input.dta"])
    @pytask.mark.produces("output.dta")
    def task_run_do_file():
        pass

If you use a dictionary to pass dependencies to the task, pytask-stata will, first, look
for a ``"source"`` key in the dictionary and, secondly, under the key ``0``.

.. code-block:: python

    @pytask.mark.depends_on({"source": "script.do", "input": "input.dta"})
    def task_run_do_file():
        pass


    # or


    @pytask.mark.depends_on({0: "script.do", "input": "input.dta"})
    def task_run_do_file():
        pass


    # or two decorators for the function, if you do not assign a name to the input.


    @pytask.mark.depends_on({"source": "script.do"})
    @pytask.mark.depends_on("input.dta")
    def task_run_do_file():
        pass



Command Line Arguments
~~~~~~~~~~~~~~~~~~~~~~

The decorator can be used to pass command line arguments to your Stata executable. For
example, pass the path of the product with

.. code-block:: python

    @pytask.mark.stata("auto.dta")
    @pytask.mark.depends_on("script.do")
    @pytask.mark.produces("auto.dta")
    def task_run_do_file():
        pass

And in your ``script.do``, you can intercept the value with

.. code-block:: do

    * Intercept command line argument and save to macro named 'produces'.
    args produces

    sysuse auto, clear
    save "`produces'"

The relative path inside the do-file works only because the pytask-stata switches the
current working directory to the directory of the do-file before the task is executed.
This is necessary precaution.

To make the task independent from the current working directory, pass the full path as
an command line argument. Here is an example.

.. code-block:: python

    # Absolute path to the build directory.
    from src.config import BLD


    @pytask.mark.stata(BLD / "auto.dta")
    @pytask.mark.depends_on("script.do")
    @pytask.mark.produces(BLD / "auto.dta")
    def task_run_do_file():
        pass


Parametrization
~~~~~~~~~~~~~~~

You can also parametrize the execution of scripts, meaning executing multiple do-files
as well as passing different command line arguments to the same do-file.

The following task executes two do-files which produce different outputs.

.. code-block:: python

    @pytask.mark.stata
    @pytask.mark.parametrize(
        "depends_on, produces", [("script_1.do", "1.dta"), ("script_2.do", "2.dta")]
    )
    def task_execute_do_file():
        pass


If you want to pass different command line arguments to the same do-file, you have to
include the ``@pytask.mark.stata`` decorator in the parametrization just like with
``@pytask.mark.depends_on`` and ``@pytask.mark.produces``.

.. code-block:: python

    @pytask.mark.depends_on("script.do")
    @pytask.mark.parametrize(
        "produces, stata",
        [("output_1.dta", ("1",)), ("output_2.dta", ("2",))],
    )
    def task_execute_do_file():
        pass


Configuration
-------------

pytask-stata can be configured with the following options.

stata_keep_log
    Use this option to keep the ``.log`` files which are produced for every task. This
    option is useful to debug Stata tasks. Set the option via the configuration file
    with

    .. code-block:: ini

        stata_keep_log = (True|true|1|False|false|0)

    The option is also available in the command line interface via the
    ``--stata-keep-log`` flag.

stata_check_log_lines
    Use this option to vary the number of lines in the log file which are checked for
    error codes. It also controls the number of lines displayed on errors. Use any
    integer greater than zero. Here is the entry in the configuration file

    .. code-block:: ini

        stata_check_log_lines = 10

    and here via the command line interface

    .. code-block:: console

        $ pytask build --stata-check-log-lines 10

stata_source_key
    If you want to change the name of the key which identifies the do file, change the
    following default configuration in your pytask configuration file.

    .. code-block:: ini

        stata_source_key = source


Changes
-------

Consult the `release notes <CHANGES.rst>`_ to find out about what is new.
