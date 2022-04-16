pytask-stata
============

.. image:: https://img.shields.io/pypi/v/pytask-stata?color=blue
    :alt: PyPI
    :target: https://pypi.org/project/pytask-stata

.. image:: https://img.shields.io/pypi/pyversions/pytask-stata
    :alt: PyPI - Python Version
    :target: https://pypi.org/project/pytask-stata

.. image:: https://img.shields.io/conda/vn/conda-forge/pytask-stata.svg
    :target: https://anaconda.org/conda-forge/pytask-stata

.. image:: https://img.shields.io/conda/pn/conda-forge/pytask-stata.svg
    :target: https://anaconda.org/conda-forge/pytask-stata

.. image:: https://img.shields.io/pypi/l/pytask-stata
    :alt: PyPI - License
    :target: https://pypi.org/project/pytask-stata

.. image:: https://img.shields.io/github/workflow/status/pytask-dev/pytask-stata/main/main
   :target: https://github.com/pytask-dev/pytask-stata/actions?query=branch%3Amain

.. image:: https://codecov.io/gh/pytask-dev/pytask-stata/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/pytask-dev/pytask-stata

.. image:: https://results.pre-commit.ci/badge/github/pytask-dev/pytask-stata/main.svg
    :target: https://results.pre-commit.ci/latest/github/pytask-dev/pytask-stata/main
    :alt: pre-commit.ci status

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

------

Run Stata's do-files with pytask.


Installation
------------

pytask-stata is available on `PyPI <https://pypi.org/project/pytask-stata>`_ and
`Anaconda.org <https://anaconda.org/conda-forge/pytask-stata>`_. Install it with

.. code-block:: console

    $ pip install pytask-stata

    # or

    $ conda install -c conda-forge pytask-stata

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


    @pytask.mark.stata(script="script.do")
    @pytask.mark.produces("auto.dta")
    def task_run_do_file():
        pass

When executing a do-file, the current working directory changes to the directory where
the script is located. This allows you, for example, to reference every data set you
want to read with a relative path from the script.


Dependencies and Products
~~~~~~~~~~~~~~~~~~~~~~~~~

Dependencies and products can be added as with a normal pytask task using the
``@pytask.mark.depends_on`` and ``@pytask.mark.produces`` decorators. which is explained
in this `tutorial
<https://pytask-dev.readthedocs.io/en/stable/tutorials/defining_dependencies_products.html>`_.


Accessing dependencies and products in the script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The decorator can be used to pass command line arguments to your Stata executable. For
example, pass the path of the product with

.. code-block:: python

    @pytask.mark.stata(script="script.do", options="auto.dta")
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

To make the task independent from the current working directory, pass the full path as
an command line argument. Here is an example.

.. code-block:: python

    # Absolute path to the build directory.
    from src.config import BLD


    @pytask.mark.stata(script="script.do", options=BLD / "auto.dta")
    @pytask.mark.produces(BLD / "auto.dta")
    def task_run_do_file():
        pass


Repeating tasks with different scripts or inputs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also parametrize the execution of scripts, meaning executing multiple do-files
as well as passing different command line arguments to the same do-file.

The following task executes two do-files which produce different outputs.

.. code-block:: python

    for i in range(2):

        @pytask.mark.task
        @pytask.mark.stata(script=f"script_{i}.do", options=f"{i}.dta")
        @pytask.mark.produces(f"{i}.dta")
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


Changes
-------

Consult the `release notes <CHANGES.rst>`_ to find out about what is new.
