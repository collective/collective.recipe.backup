"""
This module contains the tool of collective.recipe.backup
"""
from setuptools import find_packages
from setuptools import setup

import os


def read(*rnames):
    return open(os.path.join(*rnames)).read()


version = "5.0.0a1"

long_description = (
    read("README.rst") + "\n" + "Contributors\n"
    "************\n" + "\n" + read("CONTRIBUTORS.rst") + "\n" + "Change history\n"
    "**************\n" + "\n" + read("CHANGES.rst")
)
entry_point = "collective.recipe.backup:Recipe"
entry_points = {
    "zc.buildout": ["default = %s" % entry_point],
}

tests_require = [
    "zope.testing",
    "zc.buildout[test]",
    "zc.recipe.egg",
]

setup(
    name="collective.recipe.backup",
    version=version,
    description="bin/backup script: sensible defaults around bin/repozo",
    long_description=long_description,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Buildout",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: GNU General Public License (GPL)",
    ],
    keywords="buildout backup repozo zope",
    author="Reinout van Rees, Maurits van Rees",
    author_email="m.van.rees@zestsoftware.nl",
    url="https://github.com/collective/collective.recipe.backup",
    license="GPL",
    package_dir={"": "src"},
    packages=find_packages("src"),
    namespace_packages=["collective", "collective.recipe"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "zc.buildout",
        "setuptools",
        "zc.recipe.egg",
    ],
    tests_require=tests_require,
    extras_require=dict(tests=tests_require),
    test_suite="collective.recipe.backup.tests.test_docs.test_suite",
    entry_points=entry_points,
)
