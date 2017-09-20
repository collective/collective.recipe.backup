# -*-doctest-*-

Test the copyblobs.cleanup_archive function
===========================================

Import stuff.

    >>> from collective.recipe.backup.copyblobs import cleanup_archives
    >>> import time
    >>> import os

For the test, we create a backup dir using buildout's test support methods:

    >>> backup_dir = 'back'
    >>> mkdir(backup_dir)

And we'll make a function that creates a blob backup directory for
us and that also sets the file modification dates to a meaningful
time.

    >>> def add_backup(name, days=0):
    ...     global next_mod_time
    ...     write(backup_dir, name, 'dummycontents')
    ...     # Change modification time to 'days' days old.
    ...     mod_time = time.time() - (86400 * days)
    ...     os.utime(join(backup_dir, name), (mod_time, mod_time))

Calling 'cleanup_archives' without a keep arguments will just return
without doing anything.

    >>> cleanup_archives(backup_dir)

Cleaning an empty directory won't do a thing.

    >>> cleanup_archives(backup_dir, keep=1)

Adding one backup file and cleaning the directory won't remove it either:

    >>> add_backup('blob.1.tar', days=1)
    >>> cleanup_archives(backup_dir, keep=1)
    >>> ls(backup_dir)
    -  blob.1.tar

When we add a second backup directory and we keep only one then
this means the first one gets removed.

    >>> add_backup('blob.0.tar.gz', days=0)
    >>> cleanup_archives(backup_dir, keep=1)
    >>> ls(backup_dir)
    -  blob.0.tar.gz

Note that we do keep an eye on the name of the blob directories,
as unless someone has been messing manually with the names and
modification dates we only expect blob.0, blob.1, blob.2, etc, as
names, with blob.0 being the most recent.

Any files are ignored and any directories that do not match
prefix.X get ignored:

    >>> add_backup('myblob.tar.gz')
    >>> add_backup('blob.some.3.tar')
    >>> mkdir(backup_dir, 'blob.4.tar')
    >>> write(backup_dir, 'blob5.txt', 'just a file')
    >>> cleanup_archives(backup_dir, keep=1)
    >>> ls(backup_dir)
    -  blob.0.tar.gz
    d  blob.4.tar
    -  blob.some.3.tar
    -  blob5.txt
    -  myblob.tar.gz

We create a helper function that gives us a fresh directory with
some blob backup directories, where backups are made twice a day:

    >>> def fresh_backups(num, compress=False):
    ...     remove(backup_dir)
    ...     mkdir(backup_dir)
    ...     for b in range(num):
    ...         name = 'blob.%d.tar' % b
    ...         if compress:
    ...             name += '.gz'
    ...         add_backup(name, days=b / 2.0)

We keep the last 4 backups:

    >>> fresh_backups(10, compress=True)
    >>> cleanup_archives(backup_dir, keep=4)
    >>> ls(backup_dir)
    -  blob.0.tar.gz
    -  blob.1.tar.gz
    -  blob.2.tar.gz
    -  blob.3.tar.gz

    >>> fresh_backups(10)
    >>> cleanup_archives(backup_dir, keep=4)
    >>> ls(backup_dir)
    -  blob.0.tar
    -  blob.1.tar
    -  blob.2.tar
    -  blob.3.tar

Cleanup after the test.

    >>> remove(backup_dir)
