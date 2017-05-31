# -*- coding: utf-8 -*-
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
import unittest
import zc.buildout.testing
import zc.buildout.tests
import zc.recipe.egg


optionflags = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)

checker = renormalizing.RENormalizing([
    # If want to clean up the doctest output you can register
    # additional regexp normalizers here. The format is a two-tuple
    # with the RE as the first item and the replacement as the second
    # item, e.g.
    # (re.compile('my-[rR]eg[eE]ps'), 'my-regexps')
    (re.compile(r'DEBUG:.*'), ''),  # Remove DEBUG lines.
    (re.compile(r'Not SVN Repository\n'), ''),  # svn warning
    zc.buildout.testing.normalize_path,
])


def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)

    # Install the recipe in develop mode
    zc.buildout.testing.install_develop('collective.recipe.backup', test)

    # Install any other recipes that should be available in the tests
    zc.buildout.testing.install_develop('zc.recipe.egg', test)


def test_suite():
    suite = unittest.TestSuite()
    modules = [
        utils,
        repozorunner,
        collective.recipe.backup,
        copyblobs,
    ]
    for module in modules:
        suite.addTest(doctest.DocTestSuite(
            module,
            setUp=setUp,
            tearDown=zc.buildout.testing.buildoutTearDown,
            optionflags=optionflags,
            checker=checker,
        ))

    docfiles = [
        'altrestore.rst',
        'base.rst',
        'blobs.rst',
        'blob_timestamps.rst',
        'gzip.rst',
        'location.rst',
        'multiple.rst',
        'no_rsync.rst',
        'options.rst',
        'zipbackup.rst',
        'prefix.rst',
    ]
    for docfile in docfiles:
        suite.addTest(doctest.DocFileSuite(
            docfile,
            setUp=setUp,
            tearDown=zc.buildout.testing.buildoutTearDown,
            optionflags=optionflags,
            checker=checker))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
