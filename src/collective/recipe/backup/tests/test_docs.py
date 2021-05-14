"""
Doctest runner for 'collective.recipe.backup'.
"""

from collective.recipe.backup import copyblobs
from collective.recipe.backup import repozorunner
from collective.recipe.backup import utils
from zope.testing import renormalizing

# Importing modules so that we can install their eggs in the test buildout.
import collective.recipe.backup
import doctest
import re
import sys
import tempfile
import unittest
import zc.buildout.testing
import zc.buildout.tests
import zc.recipe.egg


optionflags = doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE

checker = renormalizing.RENormalizing(
    [
        # If want to clean up the doctest output you can register
        # additional regexp normalizers here. The format is a two-tuple
        # with the RE as the first item and the replacement as the second
        # item, e.g.
        # (re.compile('my-[rR]eg[eE]ps'), 'my-regexps')
        (re.compile(r"DEBUG:.*"), ""),  # Remove DEBUG lines.
        (re.compile(r"Not SVN Repository\n"), ""),  # svn warning
        # newer pip can complain:
        (re.compile(r"WARNING: Requires-Python support missing.\n"), ""),
        zc.buildout.testing.normalize_path,
    ]
)


_dummy, REPOZO_OUTPUT = tempfile.mkstemp()
REPOZO_SCRIPT_TEXT = """#!/bin/sh
echo $* >> {}""".format(
    REPOZO_OUTPUT
)


def check_repozo_output():
    # Print output and empty the file.
    with open(REPOZO_OUTPUT) as myfile:
        print(myfile.read())
    with open(REPOZO_OUTPUT, "w") as myfile:
        myfile.write("")


def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)

    # Install the recipe in develop mode
    zc.buildout.testing.install_develop("collective.recipe.backup", test)

    # Install any other recipes that should be available in the tests
    zc.buildout.testing.install_develop("zc.recipe.egg", test)

    # Add mock ``bin/repozo`` script:
    test.globs["write"]("bin", "repozo", REPOZO_SCRIPT_TEXT)
    test.globs["system"]("chmod u+x bin/repozo")

    # Create var directory:
    test.globs["mkdir"]("var")

    # Add some items to the global definitions of the test,
    # so we can access them from the doc tests.
    test.globs.update(
        {
            "check_repozo_output": check_repozo_output,
            "REPOZO_SCRIPT_TEXT": REPOZO_SCRIPT_TEXT,
        }
    )


def test_suite():
    suite = unittest.TestSuite()
    modules = [utils, repozorunner, collective.recipe.backup, copyblobs]
    for module in modules:
        suite.addTest(
            doctest.DocTestSuite(
                module,
                setUp=setUp,
                tearDown=zc.buildout.testing.buildoutTearDown,
                optionflags=optionflags,
                checker=checker,
            )
        )

    docfiles = [
        "altrestore.rst",
        "backup_blobs_archive.rst",
        "backup_blobs_dir.rst",
        "backup_blobs_dir_hard_links.rst",
        "base.rst",
        "blobs.rst",
        "blob_timestamps.rst",
        "cleanup_archives.rst",
        "cleanup_dir.rst",
        "gzip.rst",
        "incremental_blobs.rst",
        "location.rst",
        "multiple.rst",
        "no_rsync.rst",
        "options.rst",
        "prefix.rst",
        "zipbackup.rst",
    ]
    test_file = "zope2instance.rst"
    if sys.version_info[0] > 2:
        print(f"INFO: ignoring {test_file} tests on Python 3.")
        print(
            "It would pull in Zope and ZODB, which is too much for what we try to test."
        )
        print("See https://github.com/collective/collective.recipe.backup/issues/31")
    else:
        docfiles.append(test_file)
    for docfile in docfiles:
        suite.addTest(
            doctest.DocFileSuite(
                docfile,
                setUp=setUp,
                tearDown=zc.buildout.testing.buildoutTearDown,
                optionflags=optionflags,
                checker=checker,
            )
        )
    return suite


if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
