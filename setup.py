"""
This module contains the tool of collective.recipe.backup
"""

from setuptools import setup

import os


def read(*rnames):
    return open(os.path.join(*rnames)).read()


version = "6.0.0.dev0"

long_description = (
    read("README.rst") + "\n" + "Contributors\n"
    "************\n" + "\n" + read("CONTRIBUTORS.rst") + "\n" + "Change history\n"
    "**************\n" + "\n" + read("CHANGES.rst")
)

# See pyproject.toml for package metadata
setup(
    long_description=long_description,
)
