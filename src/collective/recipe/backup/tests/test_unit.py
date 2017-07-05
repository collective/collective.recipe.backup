# -*- coding: utf-8 -*-
import unittest


class UtilsTestCase(unittest.TestCase):
    """Test the code in utils.py."""

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


class CopyBlobsTestCase(unittest.TestCase):
    """Test the code in copyblobs.py."""

    def test_gen_blobdir_name(self):
        from collective.recipe.backup.copyblobs import gen_blobdir_name
        # The name starts with blobstorage and a time.
        # We only check that the century is okay.
        self.assertTrue(gen_blobdir_name().startswith('blobstorage.20'))
        # We can pass a time tuple.
        self.assertEqual(gen_blobdir_name(now=(1999, 12, 31, 23, 59, 30)),
                         'blobstorage.1999-12-31-23-59-30')
        # We can pass a different prefix.
        self.assertEqual(
            gen_blobdir_name(prefix='foo', now=(1999, 12, 31, 23, 59, 30)),
            'foo.1999-12-31-23-59-30')

    def test_gen_timestamp(self):
        from collective.recipe.backup.copyblobs import gen_timestamp
        self.assertTrue(gen_timestamp().startswith('20'))
        self.assertEqual(gen_timestamp().count('-'), 5)
        self.assertEqual(len(gen_timestamp()), 19)
        # We can pass a time tuple.
        self.assertEqual(gen_timestamp(now=(1999, 12, 31, 23, 59, 30)),
                         '1999-12-31-23-59-30')
        # We can pass an integer or float like time.time().
        self.assertEqual(gen_timestamp(now=1487874793),
                         '2017-02-23-18-33-13')
        self.assertEqual(gen_timestamp(now=1487874793.90436),
                         '2017-02-23-18-33-13')

    def test_is_time_stamp(self):
        from collective.recipe.backup.copyblobs import gen_timestamp
        from collective.recipe.backup.copyblobs import is_time_stamp
        self.assertTrue(is_time_stamp('1999-12-31-23-59-30'))
        self.assertFalse(is_time_stamp('1999-1-31-23-59-30'))
        self.assertTrue(is_time_stamp('2017-01-02-03-04-05'))
        self.assertFalse(is_time_stamp('1999-12-31'))
        self.assertFalse(is_time_stamp('99-12-31-23-59-30'))
        self.assertTrue(is_time_stamp(gen_timestamp()))

    def test_get_prefix_and_number(self):
        from collective.recipe.backup.copyblobs import get_prefix_and_number \
            as gpn
        self.assertEqual(gpn('1'), ('', '1'))
        self.assertEqual(gpn('1999-12-31-23-59-30'),
                         ('', '1999-12-31-23-59-30'))
        self.assertFalse(gpn('1', prefix='a'))
        self.assertEqual(gpn('a.1', prefix='a'), ('a', '1'))
        self.assertEqual(gpn('a.1', prefix='a.'), ('a', '1'))
        self.assertEqual(gpn('montypython.123'), ('montypython', '123'))
        self.assertEqual(gpn('a.1.tar.gz', suffixes='tar.gz'), ('a', '1'))
        self.assertEqual(
            gpn('a.1.tar.gz', suffixes=['tar', 'tar.gz']),
            ('a', '1'))
        self.assertFalse(gpn('a.1.tar.gz', suffixes=['tar', 'tgz']))
        self.assertEqual(gpn(
            'a.1999-12-31-23-59-30.tar.gz', prefix='a', suffixes='tar.gz'),
            ('a', '1999-12-31-23-59-30'))
        self.assertEqual(gpn('a.1.tar.gz', suffixes=['tar', 'tar.gz']),
                         ('a', '1'))
        self.assertEqual(gpn('a.1.tar', suffixes=['tar', 'tar.gz']),
                         ('a', '1'))
        self.assertFalse(gpn('a.1.tar.gz', suffixes=['tar', 'tgz']))

    def test_number_key(self):
        from collective.recipe.backup.copyblobs import number_key
        self.assertGreater(number_key('0'), number_key('1'))
        self.assertEqual(number_key('0'), number_key('0'))
        self.assertLess(number_key('1'), number_key('0'))
        self.assertGreater(number_key('9'), number_key('10'))
        self.assertLess(number_key('99'), number_key('10'))

        # Compare integers and timestamps.  Time stamps are more recent,
        # so they are larger.
        self.assertLess(number_key('0'), number_key('1999-12-31-23-59-30'))
        self.assertGreater(number_key('1999-12-31-23-59-30'), number_key('0'))

        # Compare timestamps.  Newest last.
        self.assertLess(
            number_key('1999-12-31-23-59-30'),
            number_key('2000-12-31-23-59-30'))
        self.assertGreater(
            number_key('2000-12-31-23-59-30'),
            number_key('1999-12-31-23-59-30'))
        self.assertEqual(
            number_key('1999-12-31-23-59-30'),
            number_key('1999-12-31-23-59-30'))

        # Check the effect on a complete sort.
        # We usually want it reversed.
        self.assertEqual(
            sorted(['0', '2', '1'], key=number_key, reverse=True),
            ['0', '1', '2'])
        self.assertEqual(
            sorted([
                '1999-12-31-23-59-30',
                '2017-01-02-03-04-05',
                '2017-10-02-03-04-05'],
                key=number_key, reverse=True),
            [
                '2017-10-02-03-04-05',
                '2017-01-02-03-04-05',
                '1999-12-31-23-59-30'])
        self.assertEqual(
            sorted([
                '0',
                '2',
                '1999-12-31-23-59-30',
                '2017-01-02-03-04-05'],
                key=number_key, reverse=True),
            [
                '2017-01-02-03-04-05',
                '1999-12-31-23-59-30',
                '0',
                '2'])

        # Test normal sorting for good measure.
        self.assertEqual(
            sorted([
                '0',
                '2',
                '1999-12-31-23-59-30',
                '2017-01-02-03-04-05'],
                key=number_key),
            [
                '2',
                '0',
                '1999-12-31-23-59-30',
                '2017-01-02-03-04-05'])

    def test_backup_key(self):
        from collective.recipe.backup.copyblobs import backup_key
        self.assertGreater(backup_key('foo.0'), backup_key('foo.1'))
        self.assertEqual(backup_key('foo.0'), backup_key('foo.0'))
        self.assertLess(backup_key('foo.1'), backup_key('foo.0'))
        self.assertGreater(backup_key('foo.9'), backup_key('foo.10'))

        # You should only compare names with the same start for directories,
        # but that is not the job of the key.
        self.assertEqual(backup_key('foo.1'), backup_key('bar.1'))

        # Compare integers and timestamps.  Time stamps are last.
        self.assertLess(
            backup_key('foo.0'), backup_key('foo.1999-12-31-23-59-30'))

        # Compare timestamps.  Newest last.
        self.assertLess(
            backup_key('foo.1999-12-31-23-59-30'),
            backup_key('foo.2000-12-31-23-59-30'))

        # It let's most of the logic be handled in number_key,
        # so let's take over one more test from there.
        self.assertEqual(
            sorted([
                'foo.0',
                'foo.2',
                'foo.1999-12-31-23-59-30',
                'foo.2017-01-02-03-04-05'],
                key=backup_key),
            [
                'foo.2',
                'foo.0',
                'foo.1999-12-31-23-59-30',
                'foo.2017-01-02-03-04-05'])

    def test_archive_backup_key(self):
        from collective.recipe.backup.copyblobs import archive_backup_key
        self.assertGreater(
            archive_backup_key('foo.0.tar.gz'),
            archive_backup_key('foo.1.tar.gz'))
        self.assertEqual(
            archive_backup_key('foo.0.tar.gz'),
            archive_backup_key('foo.0.tar.gz'))
        self.assertLess(
            archive_backup_key('foo.1.tar.gz'),
            archive_backup_key('foo.0.tar.gz'))
        self.assertGreater(
            archive_backup_key('foo.9.tar.gz'),
            archive_backup_key('foo.10.tar.gz'))

        # tar or tar.gz are both accepted.
        self.assertGreater(
            archive_backup_key('foo.0.tar.gz'),
            archive_backup_key('foo.1.tar'))
        self.assertEqual(
            archive_backup_key('foo.0.tar.gz'),
            archive_backup_key('foo.0.tar'))
        self.assertLess(
            archive_backup_key('foo.1.tar.gz'),
            archive_backup_key('foo.0.tar'))
        self.assertGreater(
            archive_backup_key('foo.9.tar.gz'),
            archive_backup_key('foo.10.tar'))

        # Compare timestamps.  Newest last.
        self.assertLess(
            archive_backup_key('foo.1999-12-31-23-59-30.tar'),
            archive_backup_key('foo.2000-12-31-23-59-30.tar.gz'))

        # You should only compare names with the same start,
        # but that is not the job of the key.
        self.assertEqual(
            archive_backup_key('foo.1.tar'),
            archive_backup_key('bar.1.tar'))

        # It shares most code with backup_key,
        # so let's take over one more test from there.
        self.assertEqual(
            sorted([
                'foo.0.tar.gz',
                'foo.2.tar.gz',
                'foo.1999-12-31-23-59-30.tar.gz',
                'foo.2017-01-02-03-04-05.tar.gz'],
                key=archive_backup_key),
            [
                'foo.2.tar.gz',
                'foo.0.tar.gz',
                'foo.1999-12-31-23-59-30.tar.gz',
                'foo.2017-01-02-03-04-05.tar.gz'])
