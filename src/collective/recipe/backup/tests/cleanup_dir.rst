# -*-doctest-*-

Test the copyblobs.cleanup function
===================================

This tests cleaning up directories.
For archives the function cleanup_archives is used.

Import stuff.

    >>> from collective.recipe.backup.copyblobs import cleanup

For the test, we create a backup dir using buildout's test support methods:

    >>> backup_dir = 'back'
    >>> mkdir(backup_dir)

And we'll make a function that creates a blob backup directory for
us and that also sets the file modification dates to a meaningful
time.

    >>> import time
    >>> import os
    >>> def add_backup(name, days=0):
    ...     mkdir(backup_dir, name)
    ...     write(backup_dir, name, 'dummyfile', 'dummycontents')
    ...     # Change modification time to 'days' days old.
    ...     mod_time = time.time() - (86400 * days)
    ...     os.utime(join(backup_dir, name), (mod_time, mod_time))

Calling 'cleanup' without a keep arguments will just return without doing
anything.

    >>> cleanup(backup_dir)

Cleaning an empty directory won't do a thing.

    >>> cleanup(backup_dir, keep=1)
    >>> cleanup(backup_dir, keep_blob_days=1)

Adding one backup file and cleaning the directory won't remove it either:

    >>> add_backup('blob.1', days=1)
    >>> cleanup(backup_dir, keep=1)
    >>> ls(backup_dir)
    d  blob.1

When we add a second backup directory and we keep only one then
this means the first one gets removed.

    >>> add_backup('blob.0', days=0)
    >>> cleanup(backup_dir, keep=1)
    >>> ls(backup_dir)
    d  blob.0

Note that we do keep an eye on the name of the blob directories,
as unless someone has been messing manually with the names and
modification dates we only expect blob.0, blob.1, blob.2, etc, as
names, with blob.0 being the most recent.

Any files are ignored and any directories that do not match
prefix.X get ignored:

    >>> add_backup('myblob')
    >>> add_backup('blob.some.3')
    >>> write(backup_dir, 'blob.4', 'just a file')
    >>> write(backup_dir, 'blob5.txt', 'just a file')
    >>> cleanup(backup_dir, keep=1)
    >>> ls(backup_dir)
    d  blob.0
    -  blob.4
    d  blob.some.3
    -  blob5.txt
    d  myblob

We do not mind what the prefix is, as long as there is only one prefix:

    >>> add_backup('myblob.4')
    >>> cleanup(backup_dir, keep=1)
    Traceback (most recent call last):
    ...
    SystemExit: 1
    >>> cleanup(backup_dir, keep_blob_days=1)
    Traceback (most recent call last):
    ...
    SystemExit: 1
    >>> ls(backup_dir)
    d  blob.0
    -  blob.4
    d  blob.some.3
    -  blob5.txt
    d  myblob
    d  myblob.4

We create a helper function that gives us a fresh directory with
some blob backup directories, where backups are made twice a day:

    >>> def fresh_backups(num):
    ...     remove(backup_dir)
    ...     mkdir(backup_dir)
    ...     for b in range(num):
    ...         name = 'blob.%d' % b
    ...         add_backup(name, days=b / 2.0)

We keep the last 4 backups:

    >>> fresh_backups(10)
    >>> cleanup(backup_dir, keep=4)
    >>> ls(backup_dir)
    d  blob.0
    d  blob.1
    d  blob.2
    d  blob.3
    >>> fresh_backups(10)

We keep the last 4 days of backups:

    >>> cleanup(backup_dir, keep_blob_days=4)
    >>> ls(backup_dir)
    d  blob.0
    d  blob.1
    d  blob.2
    d  blob.3
    d  blob.4
    d  blob.5
    d  blob.6
    d  blob.7

With full=False (the default) we ignore the keep option:

    >>> cleanup(backup_dir, full=False, keep=2, keep_blob_days=2)
    >>> ls(backup_dir)
    d  blob.0
    d  blob.1
    d  blob.2
    d  blob.3

With full=True we ignore the keep_blob_days option:

    >>> cleanup(backup_dir, full=True, keep=2, keep_blob_days=2)
    >>> ls(backup_dir)
    d  blob.0
    d  blob.1

Cleanup after the test.

    >>> remove(backup_dir)
