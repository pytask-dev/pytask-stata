from setuptools import find_packages
from setuptools import setup

setup(
    name="pytask-stata",
    version="0.0.3",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={"pytask": ["pytask_stata = pytask_stata.plugin"]},
)
