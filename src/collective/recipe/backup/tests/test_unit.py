import unittest


class UtilsTestCase(unittest.TestCase):
    """Test the code in utils.py."""

    def test_to_bool(self):
        from collective.recipe.backup import to_bool

        self.assertTrue(to_bool(True))
        self.assertFalse(to_bool(False))
        self.assertFalse(to_bool(None))
        self.assertTrue(to_bool("True"))
        self.assertTrue(to_bool("true"))
        self.assertTrue(to_bool("on"))
        self.assertFalse(to_bool("False"))
        self.assertFalse(to_bool("false"))
        self.assertFalse(to_bool(""))
        self.assertFalse(to_bool("unknown"))
        self.assertFalse(to_bool("0"))
        self.assertTrue(to_bool("1"))
        self.assertFalse(to_bool("10"))
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
            "a": "True",
            "b": "true",
            "c": "yes",
            "d": "on",
            "e": "False",
            "f": "false",
            "g": "",
            "h": "unknown",
        }
        orig_options = options.copy()
        # The result should be a unified capitalized True/False string.
        sanitised_options = {
            "a": "True",
            "b": "True",
            "c": "True",
            "d": "True",
            "e": "False",
            "f": "False",
            "g": "False",
            "h": "False",
        }
        # Without keys, nothing is changed.
        check_for_true(options, [])
        self.assertEqual(options, orig_options)
        # With some keys, some is changed.
        check_for_true(options, ["a", "c"])
        self.assertNotEqual(options, orig_options)
        self.assertNotEqual(options, sanitised_options)
        self.assertEqual(options["a"], "True")
        self.assertEqual(options["c"], "True")
        # Without all keys, everything is changed.
        check_for_true(options, options.keys())
        self.assertEqual(options, sanitised_options)

    def test_get_zope_option(self):
        from collective.recipe.backup import get_zope_option

        # The buildout dictionary we pass, is quite specific.
        buildout_info = {
            "buildout": {"parts": "one two four"},
            "one": {
                "recipe": "unknown.recipe",
                "wanted": "one-wanted",
                "one-only": "one-only-value",
            },
            "two": {
                "recipe": "plone.recipe.zeoserver",
                "wanted": "two-wanted",
                "two-only": "two-only-value",
            },
            "three": {
                "recipe": "plone.recipe.zeoserver",
                "wanted": "three-wanted",
                "three-only": "three-only-value",
            },
            "four": {
                "recipe": "plone.recipe.zope2INSTANCE",
                "wanted": "four-wanted",
                "four-only": "four-only-value",
            },
        }
        # Non existing keys are not found:
        self.assertFalse(get_zope_option(buildout_info, "foo"))
        # Only keys from one of the correct recipes are found:
        self.assertFalse(get_zope_option(buildout_info, "one-only"))
        self.assertEqual(get_zope_option(buildout_info, "wanted"), "two-wanted")
        # Keys from a non active part are not found:
        self.assertFalse(get_zope_option(buildout_info, "three-only"))
        # We accept recipes with mixed case:
        self.assertEqual(get_zope_option(buildout_info, "four-only"), "four-only-value")
        # The order of parts is important:
        buildout_info["buildout"] = {"parts": "four two one"}
        self.assertEqual(get_zope_option(buildout_info, "wanted"), "four-wanted")


class CopyBlobsTestCase(unittest.TestCase):
    """Test the code in copyblobs.py."""

    def test_gen_timestamp(self):
        from collective.recipe.backup.copyblobs import gen_timestamp

        self.assertTrue(gen_timestamp().startswith("20"))
        self.assertEqual(gen_timestamp().count("-"), 5)
        self.assertEqual(len(gen_timestamp()), 19)
        # We can pass a time tuple.
        self.assertEqual(
            gen_timestamp(now=(1999, 12, 31, 23, 59, 30)), "1999-12-31-23-59-30"
        )
        # We can pass an integer or float like time.time().
        self.assertEqual(gen_timestamp(now=1487874793), "2017-02-23-18-33-13")
        self.assertEqual(gen_timestamp(now=1487874793.90436), "2017-02-23-18-33-13")

    def test_is_time_stamp(self):
        from collective.recipe.backup.copyblobs import gen_timestamp
        from collective.recipe.backup.copyblobs import is_time_stamp

        self.assertTrue(is_time_stamp("1999-12-31-23-59-30"))
        self.assertFalse(is_time_stamp("1999-1-31-23-59-30"))
        self.assertTrue(is_time_stamp("2017-01-02-03-04-05"))
        self.assertFalse(is_time_stamp("1999-12-31"))
        self.assertFalse(is_time_stamp("99-12-31-23-59-30"))
        self.assertTrue(is_time_stamp(gen_timestamp()))

    def test_get_prefix_and_number(self):
        from collective.recipe.backup.copyblobs import get_prefix_and_number as gpn

        self.assertEqual(gpn("1"), ("", "1"))
        self.assertEqual(gpn("1999-12-31-23-59-30"), ("", "1999-12-31-23-59-30"))
        self.assertFalse(gpn("1", prefix="a"))
        self.assertEqual(gpn("a.1", prefix="a"), ("a", "1"))
        self.assertEqual(gpn("a.1", prefix="a."), ("a", "1"))
        self.assertEqual(gpn("montypython.123"), ("montypython", "123"))
        self.assertEqual(gpn("a.1.tar.gz", suffixes="tar.gz"), ("a", "1"))
        self.assertEqual(gpn("a.1.tar.gz", suffixes=["tar", "tar.gz"]), ("a", "1"))
        self.assertFalse(gpn("a.1.tar.gz", suffixes=["tar", "tgz"]))
        self.assertEqual(
            gpn("a.1999-12-31-23-59-30.tar.gz", prefix="a", suffixes="tar.gz"),
            ("a", "1999-12-31-23-59-30"),
        )
        self.assertEqual(gpn("a.1.tar.gz", suffixes=["tar", "tar.gz"]), ("a", "1"))
        self.assertEqual(gpn("a.1.tar", suffixes=["tar", "tar.gz"]), ("a", "1"))
        self.assertFalse(gpn("a.1.tar.gz", suffixes=["tar", "tgz"]))
        # The order of the suffixes should not matter.
        self.assertEqual(
            gpn(
                "a.1.delta.tar.gz",
                suffixes=["delta.tar.gz", "delta.tar", "tar", "tar.gz"],
            ),
            ("a", "1"),
        )
        self.assertEqual(
            gpn(
                "a.1.delta.tar.gz",
                suffixes=["tar", "tar.gz", "delta.tar.gz", "delta.tar"],
            ),
            ("a", "1"),
        )

    def test_number_key(self):
        from collective.recipe.backup.copyblobs import number_key

        self.assertGreater(number_key("0"), number_key("1"))
        self.assertEqual(number_key("0"), number_key("0"))
        self.assertLess(number_key("1"), number_key("0"))
        self.assertGreater(number_key("9"), number_key("10"))
        self.assertLess(number_key("99"), number_key("10"))

        # Compare integers and timestamps.  Time stamps are more recent,
        # so they are larger.
        self.assertLess(number_key("0"), number_key("1999-12-31-23-59-30"))
        self.assertGreater(number_key("1999-12-31-23-59-30"), number_key("0"))

        # Compare timestamps.  Newest last.
        self.assertLess(
            number_key("1999-12-31-23-59-30"), number_key("2000-12-31-23-59-30")
        )
        self.assertGreater(
            number_key("2000-12-31-23-59-30"), number_key("1999-12-31-23-59-30")
        )
        self.assertEqual(
            number_key("1999-12-31-23-59-30"), number_key("1999-12-31-23-59-30")
        )

        # Check the effect on a complete sort.
        # We usually want it reversed.
        self.assertEqual(
            sorted(["0", "2", "1"], key=number_key, reverse=True), ["0", "1", "2"]
        )
        self.assertEqual(
            sorted(
                ["1999-12-31-23-59-30", "2017-01-02-03-04-05", "2017-10-02-03-04-05"],
                key=number_key,
                reverse=True,
            ),
            ["2017-10-02-03-04-05", "2017-01-02-03-04-05", "1999-12-31-23-59-30"],
        )
        self.assertEqual(
            sorted(
                ["0", "2", "1999-12-31-23-59-30", "2017-01-02-03-04-05"],
                key=number_key,
                reverse=True,
            ),
            ["2017-01-02-03-04-05", "1999-12-31-23-59-30", "0", "2"],
        )

        # Test normal sorting for good measure.
        self.assertEqual(
            sorted(
                ["0", "2", "1999-12-31-23-59-30", "2017-01-02-03-04-05"], key=number_key
            ),
            ["2", "0", "1999-12-31-23-59-30", "2017-01-02-03-04-05"],
        )

    def test_first_number_key(self):
        from collective.recipe.backup.copyblobs import first_number_key
        from collective.recipe.backup.copyblobs import is_snar
        from collective.recipe.backup.copyblobs import mod_time_number_key

        # Values should be (number, modification time, ignored extra).
        # Number is either a number or a timestamp.
        self.assertGreater(first_number_key(("0", 0)), first_number_key(("1", 0)))
        self.assertEqual(first_number_key(("0", 0)), first_number_key(("0", 0)))
        self.assertLess(first_number_key(("1", 0)), first_number_key(("0", 0)))
        self.assertGreater(first_number_key(("9", 0)), first_number_key(("10", 0)))
        self.assertLess(first_number_key(("99", 0)), first_number_key(("10", 0)))

        # When the number is the same, the modification time becomes relevant.
        self.assertGreater(first_number_key(("0", 1)), first_number_key(("0", 0)))
        self.assertLess(first_number_key(("0", 0)), first_number_key(("0", 1)))

        # Check the effect on a complete sort.
        # We usually want it reversed.
        # Use some actual data from a test that used to fail.
        data = [
            (
                "2016-12-25-00-00-00",
                1506465957.3800716,
                "blobstorage.2016-12-25-00-00-00.tar",
            ),
            (
                "2016-12-25-00-00-00",
                1506465958.8960717,
                "blobstorage.2016-12-25-00-00-00.snar",
            ),
            (
                "2016-12-26-00-00-00",
                1506465958.8960717,
                "blobstorage.2016-12-26-00-00-00.delta.tar",
            ),
        ]
        correct_order = [
            # First the delta, which has the latest timestamp number.
            (
                "2016-12-26-00-00-00",
                1506465958.8960717,
                "blobstorage.2016-12-26-00-00-00.delta.tar",
            ),
            # Then the snar, was was created at the same as the full tar,
            # but was modified at the same time as the delta.
            (
                "2016-12-25-00-00-00",
                1506465958.8960717,
                "blobstorage.2016-12-25-00-00-00.snar",
            ),
            # Lastly the tar, which has the oldest timestamp number,
            # just like the snar, but has an older modification time.
            (
                "2016-12-25-00-00-00",
                1506465957.3800716,
                "blobstorage.2016-12-25-00-00-00.tar",
            ),
        ]
        self.assertEqual(
            sorted(data, key=first_number_key, reverse=True), correct_order
        )
        self.assertEqual(
            sorted(data, key=mod_time_number_key, reverse=True), correct_order
        )

        # And another one.
        data = [
            (
                "2017-09-27-13-00-58",
                1506517817.0,
                "/blobstorage.2017-09-27-13-00-58.snar",
            ),
            (
                "2017-09-27-13-00-58",
                1506517561.0,
                "/blobstorage.2017-09-27-13-00-58.tar",
            ),
            (
                "2017-09-27-13-08-04",
                1506517684.0,
                "/blobstorage.2017-09-27-13-08-04.delta.tar",
            ),
            (
                "2017-09-27-13-10-17",
                1506517817.0,
                "/blobstorage.2017-09-27-13-10-17.delta.tar",
            ),
        ]
        correct_order_by_number = [
            # delta 2: highest number, last modified
            (
                "2017-09-27-13-10-17",
                1506517817.0,
                "/blobstorage.2017-09-27-13-10-17.delta.tar",
            ),
            # delta 1: all in between
            (
                "2017-09-27-13-08-04",
                1506517684.0,
                "/blobstorage.2017-09-27-13-08-04.delta.tar",
            ),
            # snar: lowest number, last modified
            (
                "2017-09-27-13-00-58",
                1506517817.0,
                "/blobstorage.2017-09-27-13-00-58.snar",
            ),
            # tar: lowest number, oldest modified
            (
                "2017-09-27-13-00-58",
                1506517561.0,
                "/blobstorage.2017-09-27-13-00-58.tar",
            ),
        ]
        correct_order_by_mod_time = [
            # delta 2: last modified, highest number
            (
                "2017-09-27-13-10-17",
                1506517817.0,
                "/blobstorage.2017-09-27-13-10-17.delta.tar",
            ),
            # snar: last modified, lowest number
            (
                "2017-09-27-13-00-58",
                1506517817.0,
                "/blobstorage.2017-09-27-13-00-58.snar",
            ),
            # delta 1: all in between
            (
                "2017-09-27-13-08-04",
                1506517684.0,
                "/blobstorage.2017-09-27-13-08-04.delta.tar",
            ),
            # tar: oldest modified, lowest number
            (
                "2017-09-27-13-00-58",
                1506517561.0,
                "/blobstorage.2017-09-27-13-00-58.tar",
            ),
        ]
        # We use this in a part of the code that wants these to be the same,
        # but that is not the case.  Without snapshot archives it is
        # the same though.
        self.assertNotEqual(correct_order_by_number, correct_order_by_mod_time)
        self.assertEqual(
            [x for x in correct_order_by_number if not is_snar(x[2])],
            [x for x in correct_order_by_mod_time if not is_snar(x[2])],
        )
        self.assertEqual(
            sorted(data, key=first_number_key, reverse=True), correct_order_by_number
        )
        self.assertEqual(
            sorted(data, key=mod_time_number_key, reverse=True),
            correct_order_by_mod_time,
        )

    def test_backup_key(self):
        from collective.recipe.backup.copyblobs import backup_key

        self.assertGreater(backup_key("foo.0"), backup_key("foo.1"))
        self.assertEqual(backup_key("foo.0"), backup_key("foo.0"))
        self.assertLess(backup_key("foo.1"), backup_key("foo.0"))
        self.assertGreater(backup_key("foo.9"), backup_key("foo.10"))

        # You should only compare names with the same start for directories,
        # but that is not the job of the key.
        self.assertEqual(backup_key("foo.1"), backup_key("bar.1"))

        # Compare integers and timestamps.  Time stamps are last.
        self.assertLess(backup_key("foo.0"), backup_key("foo.1999-12-31-23-59-30"))

        # Compare timestamps.  Newest last.
        self.assertLess(
            backup_key("foo.1999-12-31-23-59-30"), backup_key("foo.2000-12-31-23-59-30")
        )

        # It let's most of the logic be handled in number_key,
        # so let's take over one more test from there.
        self.assertEqual(
            sorted(
                [
                    "foo.0",
                    "foo.2",
                    "foo.1999-12-31-23-59-30",
                    "foo.2017-01-02-03-04-05",
                ],
                key=backup_key,
            ),
            ["foo.2", "foo.0", "foo.1999-12-31-23-59-30", "foo.2017-01-02-03-04-05"],
        )

    def test_archive_backup_key(self):
        from collective.recipe.backup.copyblobs import archive_backup_key

        self.assertGreater(
            archive_backup_key("foo.0.tar.gz"), archive_backup_key("foo.1.tar.gz")
        )
        self.assertEqual(
            archive_backup_key("foo.0.tar.gz"), archive_backup_key("foo.0.tar.gz")
        )
        self.assertLess(
            archive_backup_key("foo.1.tar.gz"), archive_backup_key("foo.0.tar.gz")
        )
        self.assertGreater(
            archive_backup_key("foo.9.tar.gz"), archive_backup_key("foo.10.tar.gz")
        )

        # tar or tar.gz are both accepted.
        self.assertGreater(
            archive_backup_key("foo.0.tar.gz"), archive_backup_key("foo.1.tar")
        )
        self.assertEqual(
            archive_backup_key("foo.0.tar.gz"), archive_backup_key("foo.0.tar")
        )
        self.assertLess(
            archive_backup_key("foo.1.tar.gz"), archive_backup_key("foo.0.tar")
        )
        self.assertGreater(
            archive_backup_key("foo.9.tar.gz"), archive_backup_key("foo.10.tar")
        )

        # Compare timestamps.  Newest last.
        self.assertLess(
            archive_backup_key("foo.1999-12-31-23-59-30.tar"),
            archive_backup_key("foo.2000-12-31-23-59-30.tar.gz"),
        )

        # You should only compare names with the same start,
        # but that is not the job of the key.
        self.assertEqual(
            archive_backup_key("foo.1.tar"), archive_backup_key("bar.1.tar")
        )

        # It shares most code with backup_key,
        # so let's take over one more test from there.
        self.assertEqual(
            sorted(
                [
                    "foo.0.tar.gz",
                    "foo.2.tar.gz",
                    "foo.1999-12-31-23-59-30.tar.gz",
                    "foo.2017-01-02-03-04-05.tar.gz",
                ],
                key=archive_backup_key,
            ),
            [
                "foo.2.tar.gz",
                "foo.0.tar.gz",
                "foo.1999-12-31-23-59-30.tar.gz",
                "foo.2017-01-02-03-04-05.tar.gz",
            ],
        )

    def test_combine_backups(self):
        from collective.recipe.backup.copyblobs import combine_backups as cb

        self.assertEqual(cb([]), [])
        # The list should have lists/tuples of (num, mod_time, path).
        # Modification times are not relevant here.
        # Num can be 0, 1, etc, or a timestamp.
        # They are already sorted with most recent first.
        # They can be tars, deltas, snars, directories,
        # although the function should not be needed for directories.
        self.assertEqual(cb([(0, 0, "a.tar")]), [[(0, 0, "a.tar")]])
        self.assertEqual(
            cb(
                [
                    (0, 0, "a.tar"),
                    (0, 0, "b.tar.gz"),
                    (0, 0, "a.tar.gz"),
                    (0, 0, "b.tar"),
                ]
            ),
            [
                [(0, 0, "a.tar")],
                [(0, 0, "b.tar.gz")],
                [(0, 0, "a.tar.gz")],
                [(0, 0, "b.tar")],
            ],
        )
        self.assertEqual(
            cb([(0, 0, "a.tar"), (0, 0, "b.tar")]),
            [[(0, 0, "a.tar")], [(0, 0, "b.tar")]],
        )
        self.assertEqual(
            cb([(0, 0, "dir1"), (0, 0, "dir2")]), [[(0, 0, "dir1")], [(0, 0, "dir2")]]
        )
        # Deltas and tars are combined:
        self.assertEqual(
            cb([(0, 0, "a.delta.tar"), (0, 0, "b.tar")]),
            [[(0, 0, "a.delta.tar"), (0, 0, "b.tar")]],
        )
        self.assertEqual(
            cb(
                [
                    (0, 0, "a.delta.tar"),
                    (0, 0, "b.tar"),
                    (0, 0, "c.delta.tar"),
                    (0, 0, "d.delta.tar"),
                    (0, 0, "e.tar"),
                ]
            ),
            [
                [(0, 0, "a.delta.tar"), (0, 0, "b.tar")],
                [(0, 0, "c.delta.tar"), (0, 0, "d.delta.tar"), (0, 0, "e.tar")],
            ],
        )
        # Snars (snapshot archives) and tars are combined:
        self.assertEqual(
            cb([(0, 0, "a.delta.tar"), (0, 0, "b.tar")]),
            [[(0, 0, "a.delta.tar"), (0, 0, "b.tar")]],
        )
        self.assertEqual(
            cb(
                [
                    (0, 0, "a.snar"),
                    (0, 0, "b.tar"),
                    # lonely snar, which is strange but should not break:
                    (0, 0, "c.snar"),
                    (0, 0, "d.snar"),
                    (0, 0, "e.tar"),
                ]
            ),
            [
                [(0, 0, "a.snar"), (0, 0, "b.tar")],
                [(0, 0, "c.snar")],
                [(0, 0, "d.snar"), (0, 0, "e.tar")],
            ],
        )
        # The order of snar and tar should not matter:
        # two that belong together are expected to have the same base name,
        # which means they have the same sort key.
        self.assertEqual(
            cb(
                [
                    (0, 0, "a.tar"),
                    (0, 0, "b.snar"),
                    # lonely tar, which is strange but should not break:
                    (0, 0, "c.tar"),
                    (0, 0, "d.tar"),
                    (0, 0, "e.snar"),
                ]
            ),
            [
                [(0, 0, "a.tar"), (0, 0, "b.snar")],
                [(0, 0, "c.tar")],
                [(0, 0, "d.tar"), (0, 0, "e.snar")],
            ],
        )
        # Deltas, tars and snars are combined:
        self.assertEqual(
            cb([(0, 0, "a.delta.tar"), (0, 0, "b.tar"), (0, 0, "b.snar")]),
            [[(0, 0, "a.delta.tar"), (0, 0, "b.tar"), (0, 0, "b.snar")]],
        )
        self.assertEqual(
            cb([(0, 0, "a.delta.tar"), (0, 0, "b.snar"), (0, 0, "b.tar")]),
            [[(0, 0, "a.delta.tar"), (0, 0, "b.snar"), (0, 0, "b.tar")]],
        )
        self.assertEqual(
            cb(
                [
                    (0, 0, "a.delta.tar"),
                    (0, 0, "b.tar"),
                    (0, 0, "c.snar"),
                    (0, 0, "d.delta.tar"),
                    (0, 0, "e.delta.tar.gz"),
                    (0, 0, "f.snar"),
                    (0, 0, "g.tar.gz"),
                ]
            ),
            [
                [(0, 0, "a.delta.tar"), (0, 0, "b.tar"), (0, 0, "c.snar")],
                [
                    (0, 0, "d.delta.tar"),
                    (0, 0, "e.delta.tar.gz"),
                    (0, 0, "f.snar"),
                    (0, 0, "g.tar.gz"),
                ],
            ],
        )
