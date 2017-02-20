# -*- coding: utf-8 -*-
import unittest


class UtilsTestCase(unittest.TestCase):

    def test_to_bool(self):
        from collective.recipe.backup import to_bool
        self.assertTrue(to_bool(True))
        self.assertFalse(to_bool(False))
        self.assertFalse(to_bool(None))
        self.assertTrue(to_bool('True'))
        self.assertTrue(to_bool('true'))
        self.assertTrue(to_bool('on'))
        self.assertFalse(to_bool('False'))
        self.assertFalse(to_bool('false'))
        self.assertFalse(to_bool(''))
        self.assertFalse(to_bool('unknown'))
        self.assertFalse(to_bool('0'))
        self.assertTrue(to_bool('1'))
        self.assertFalse(to_bool('10'))
        self.assertFalse(to_bool(0))
        self.assertTrue(to_bool(-1))
        self.assertTrue(to_bool(42))

    def test_check_for_true(self):
        from collective.recipe.backup import check_for_true
        # check_for_true changes the input in place.
        self.assertEqual(check_for_true({}, []), None)
        options = {}
        check_for_true(options, [])
        self.assertEqual(options, {})
        options = {
            'a': 'True',
            'b': 'true',
            'c': 'yes',
            'd': 'on',
            'e': 'False',
            'f': 'false',
            'g': '',
            'h': 'unknown',
        }
        orig_options = options.copy()
        # The result should be a unified capitalized True/False string.
        sanitised_options = {
            'a': 'True',
            'b': 'True',
            'c': 'True',
            'd': 'True',
            'e': 'False',
            'f': 'False',
            'g': 'False',
            'h': 'False',
        }
        # Without keys, nothing is changed.
        check_for_true(options, [])
        self.assertEqual(options, orig_options)
        # With some keys, some is changed.
        check_for_true(options, ['a', 'c'])
        self.assertNotEqual(options, orig_options)
        self.assertNotEqual(options, sanitised_options)
        self.assertEqual(options['a'], 'True')
        self.assertEqual(options['c'], 'True')
        # Without all keys, everything is changed.
        check_for_true(options, options.keys())
        self.assertEqual(options, sanitised_options)

    def test_get_zope_option(self):
        from collective.recipe.backup import get_zope_option
        # The buildout dictionary we pass, is quite specific.
        buildout_info = {
            'buildout': {'parts': 'one two four'},
            'one': {
                'recipe': 'unknown.recipe',
                'wanted': 'one-wanted',
                'one-only': 'one-only-value',
            },
            'two': {
                'recipe': 'plone.recipe.zeoserver',
                'wanted': 'two-wanted',
                'two-only': 'two-only-value',
            },
            'three': {
                'recipe': 'plone.recipe.zeoserver',
                'wanted': 'three-wanted',
                'three-only': 'three-only-value',
            },
            'four': {
                'recipe': 'plone.recipe.zope2INSTANCE',
                'wanted': 'four-wanted',
                'four-only': 'four-only-value',
            },
        }
        # Non existing keys are not found:
        self.assertFalse(get_zope_option(buildout_info, 'foo'))
        # Only keys from one of the correct recipes are found:
        self.assertFalse(get_zope_option(buildout_info, 'one-only'))
        self.assertEqual(
            get_zope_option(buildout_info, 'wanted'), 'two-wanted')
        # Keys from a non active part are not found:
        self.assertFalse(get_zope_option(buildout_info, 'three-only'))
        # We accept recipes with mixed case:
        self.assertEqual(
            get_zope_option(buildout_info, 'four-only'), 'four-only-value')
        # The order of parts is important:
        buildout_info['buildout'] = {'parts': 'four two one'}
        self.assertEqual(
            get_zope_option(buildout_info, 'wanted'), 'four-wanted')
