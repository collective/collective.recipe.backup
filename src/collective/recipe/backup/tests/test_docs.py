# -*- coding: utf-8 -*-
"""
Doctest runner for 'collective.recipe.backup'.
"""
__docformat__ = 'restructuredtext'

import re
import unittest
import zc.buildout.tests
import zc.buildout.testing
import collective.recipe.backup
from collective.recipe.backup import repozorunner
from collective.recipe.backup import copyblobs
from zope.testing import doctest, renormalizing

# Importing modules so that we can install their eggs in the test buildout.
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
    zc.buildout.testing.normalize_path,
    ])


def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)

    # Install the recipe in develop mode
    zc.buildout.testing.install_develop('collective.recipe.backup', test)

    # Install any other recipes that should be available in the tests
    zc.buildout.testing.install_develop('zc.recipe.egg', test)


def test_suite():
    suite = unittest.TestSuite((
            doctest.DocFileSuite(
                '../README.txt',
                setUp=setUp,
                tearDown=zc.buildout.testing.buildoutTearDown,
                optionflags=optionflags,
                checker=checker,
                ),
            doctest.DocTestSuite(
                repozorunner,
                setUp=setUp,
                tearDown=zc.buildout.testing.buildoutTearDown,
                optionflags=optionflags,
                checker=checker,
                ),
            doctest.DocTestSuite(
                collective.recipe.backup,
                setUp=setUp,
                tearDown=zc.buildout.testing.buildoutTearDown,
                optionflags=optionflags,
                checker=checker,
                ),
            doctest.DocTestSuite(
                copyblobs,
                setUp=setUp,
                tearDown=zc.buildout.testing.buildoutTearDown,
                optionflags=optionflags,
                checker=checker,
                ),
            ))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
