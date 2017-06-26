# -*-doctest-*-

Advanced usage: multiple Data.fs files
======================================

Just to isolate some test differences, we run an empty buildout once::

    >>> ignore = system(buildout)

Add mock ``bin/repozo`` script::

    >>> import sys
    >>> write('bin', 'repozo',
    ...       "#!%s\nimport sys\nprint ' '.join(sys.argv[1:])" % sys.executable)
    >>> dontcare = system('chmod u+x bin/repozo')

Create var directory::

    >>> mkdir('var')

Sometimes, a Data.fs is split into several files. Most common reason is to
have a regular Data.fs and a catalog.fs which contains the
portal_catalog. This is supported with the ``additional_filestorages``
option::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... additional_filestorages =
    ...     catalog
    ...     another
    ...     foo/bar
    ... """)

The additional backups have to be stored separate from the ``Data.fs``
backup. That's done by appending the file's name and creating extra backup
directories named that way::

    >>> print system(buildout)
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    <BLANKLINE>
    >>> ls('var')

The various backups are done one after the other. They cannot be done at the
same time with repozo. So they are not completely in sync. The "other"
databases are backed up first as a small difference in the catalog is just
mildly irritating, but the other way around users can get real errors::

    >>> print system('bin/backup')
    --backup -f /sample-buildout/var/filestorage/catalog.fs -r /sample-buildout/var/backups_catalog --quick --gzip
    --backup -f /sample-buildout/var/filestorage/another.fs -r /sample-buildout/var/backups_another --quick --gzip
    --backup -f /sample-buildout/var/filestorage/foo/bar.fs -r /sample-buildout/var/backups_foo/bar --quick --gzip
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups --quick --gzip
    INFO: Created /sample-buildout/var/backups_catalog
    INFO: Created /sample-buildout/var/backups_another
    INFO: Created /sample-buildout/var/backups_foo/bar
    INFO: Created /sample-buildout/var/backups
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/catalog.fs to /sample-buildout/var/backups_catalog
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/another.fs to /sample-buildout/var/backups_another
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/foo/bar.fs to /sample-buildout/var/backups_foo/bar
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/backups
    <BLANKLINE>
    >>> ls('var')
    d  backups
    d  backups_another
    d  backups_catalog
    d  backups_foo

Same with snapshot backups::

    >>> print system('bin/snapshotbackup')
    --backup -f /sample-buildout/var/filestorage/catalog.fs -r /sample-buildout/var/snapshotbackups_catalog -F --gzip
    --backup -f /sample-buildout/var/filestorage/another.fs -r /sample-buildout/var/snapshotbackups_another -F --gzip
    --backup -f /sample-buildout/var/filestorage/foo/bar.fs -r /sample-buildout/var/snapshotbackups_foo/bar -F --gzip
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/snapshotbackups -F --gzip
    INFO: Created /sample-buildout/var/snapshotbackups_catalog
    INFO: Created /sample-buildout/var/snapshotbackups_another
    INFO: Created /sample-buildout/var/snapshotbackups_foo/bar
    INFO: Created /sample-buildout/var/snapshotbackups
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/catalog.fs to /sample-buildout/var/snapshotbackups_catalog
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/another.fs to /sample-buildout/var/snapshotbackups_another
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/foo/bar.fs to /sample-buildout/var/snapshotbackups_foo/bar
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/snapshotbackups
    <BLANKLINE>

And a restore restores all three backups::

    >>> print system('bin/restore', input='yes\n')
    --recover -o /sample-buildout/var/filestorage/catalog.fs -r /sample-buildout/var/backups_catalog
    --recover -o /sample-buildout/var/filestorage/another.fs -r /sample-buildout/var/backups_another
    --recover -o /sample-buildout/var/filestorage/foo/bar.fs -r /sample-buildout/var/backups_foo/bar
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/catalog.fs
        /sample-buildout/var/filestorage/another.fs
        /sample-buildout/var/filestorage/foo/bar.fs
        /sample-buildout/var/filestorage/Data.fs
    Are you sure? (yes/No)?
    INFO: Created directory /sample-buildout/var/filestorage
    INFO: Created directory /sample-buildout/var/filestorage/foo
    INFO: Please wait while restoring database file: /sample-buildout/var/backups_catalog to /sample-buildout/var/filestorage/catalog.fs
    INFO: Please wait while restoring database file: /sample-buildout/var/backups_another to /sample-buildout/var/filestorage/another.fs
    INFO: Please wait while restoring database file: /sample-buildout/var/backups_foo/bar to /sample-buildout/var/filestorage/foo/bar.fs
    INFO: Please wait while restoring database file: /sample-buildout/var/backups to /sample-buildout/var/filestorage/Data.fs
    <BLANKLINE>

We fake three old backups in all the (snapshot)backup directories to
test if the 'keep' parameter is working correctly.

    >>> import os
    >>> import time
    >>> next_mod_time = time.time() - 1000
    >>> def add_backup(dir, name):  # same as in the tests in repozorunner.py
    ...     global next_mod_time
    ...     write(dir, name, 'sample fs')
    ...     # Change modification time, every new file is 10 seconds older.
    ...     os.utime(join(dir, name), (next_mod_time, next_mod_time))
    ...     next_mod_time += 10
    >>> dirs = ('var/backups', 'var/snapshotbackups')
    >>> for tail in ('', '_catalog', '_another', '_foo/bar'):
    ...     for dir in dirs:
    ...         dir = dir + tail
    ...         for i in reversed(range(3)):
    ...             add_backup(dir, '%d.fs' % i)
    >>> ls('var/backups')  # Before
    -  0.fs
    -  1.fs
    -  2.fs
    >>> print system('bin/backup')
    --backup -f /sample-buildout/var/filestorage/catalog.fs -r /sample-buildout/var/backups_catalog --quick --gzip
    --backup -f /sample-buildout/var/filestorage/another.fs -r /sample-buildout/var/backups_another --quick --gzip
    --backup -f /sample-buildout/var/filestorage/foo/bar.fs -r /sample-buildout/var/backups_foo/bar --quick --gzip
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups --quick --gzip
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/catalog.fs to /sample-buildout/var/backups_catalog
    INFO: Removed 1 file(s) belonging to old backups, the latest 2 full backups have been kept.
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/another.fs to /sample-buildout/var/backups_another
    INFO: Removed 1 file(s) belonging to old backups, the latest 2 full backups have been kept.
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/foo/bar.fs to /sample-buildout/var/backups_foo/bar
    INFO: Removed 1 file(s) belonging to old backups, the latest 2 full backups have been kept.
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/backups
    INFO: Removed 1 file(s) belonging to old backups, the latest 2 full backups have been kept.
    <BLANKLINE>
    >>> ls('var/backups')  # After
    -  0.fs
    -  1.fs

Same for the snapshot backups:

    >>> print system('bin/snapshotbackup')
    --backup -f /sample-buildout/var/filestorage/catalog.fs -r /sample-buildout/var/snapshotbackups_catalog -F --gzip
    --backup -f /sample-buildout/var/filestorage/another.fs -r /sample-buildout/var/snapshotbackups_another -F --gzip
    --backup -f /sample-buildout/var/filestorage/foo/bar.fs -r /sample-buildout/var/snapshotbackups_foo/bar -F --gzip
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/snapshotbackups -F --gzip
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/catalog.fs to /sample-buildout/var/snapshotbackups_catalog
    INFO: Removed 1 file(s) belonging to old backups, the latest 2 full backups have been kept.
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/another.fs to /sample-buildout/var/snapshotbackups_another
    INFO: Removed 1 file(s) belonging to old backups, the latest 2 full backups have been kept.
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/foo/bar.fs to /sample-buildout/var/snapshotbackups_foo/bar
    INFO: Removed 1 file(s) belonging to old backups, the latest 2 full backups have been kept.
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/snapshotbackups
    INFO: Removed 1 file(s) belonging to old backups, the latest 2 full backups have been kept.
    <BLANKLINE>
