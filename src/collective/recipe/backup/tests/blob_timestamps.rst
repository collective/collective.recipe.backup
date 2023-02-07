# -*-doctest-*-

Blob storage with timestamps
============================

These are tests with ``blob_timestamps = true``.
This started as a copy of the ``blobs.rst`` file.
Several corner cases are only tested in that file, not in the current one.

Some imports:

    >>> import os

Write a buildout config::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... # For some reason this is now needed:
    ... index = https://pypi.python.org/simple
    ... # Avoid suddenly updating zc.buildout or other packages:
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... blob_timestamps = true
    ... keep = 3
    ... """)
    >>> print(system(buildout))
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    <BLANKLINE>
    >>> ls('bin')
    -  backup
    -  buildout
    -  repozo
    -  restore
    -  snapshotbackup
    -  snapshotrestore
    >>> mkdir('var', 'filestorage')
    >>> mkdir('var', 'blobstorage')
    >>> write('var', 'blobstorage', 'blob1.txt', 'Sample blob 1.')

Mock some repozo backups with timestamps.
In this way we can check that our logic for matching a blobstorage backup and filestorage backup works.
And it is easier to write the tests with a real date rather than 20...-...-...-...-...-...

    >>> mkdir('var', 'snapshotbackups')
    >>> write('var', 'snapshotbackups', '1999-12-31-01-01-03.fsz', 'mock datafs backup')

Test the snapshotbackup first, as that should be easiest.

    >>> print(system('bin/snapshotbackup'))
    INFO: Created /sample-buildout/var/blobstoragesnapshots
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/snapshotbackups
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots
    INFO: rsync -a  /sample-buildout/var/blobstorage /sample-buildout/var/blobstoragesnapshots/blobstorage.1999-12-31-01-01-03
    INFO: Creating symlink from latest to blobstorage.1999-12-31-01-01-03
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/snapshotbackups -F --gzip
    >>> ls('var', 'blobstoragesnapshots')
    d  blobstorage.1999-12-31-01-01-03
    d  latest
    >>> timestamp0 = 'blobstorage.1999-12-31-01-01-03'
    >>> ls('var', 'blobstoragesnapshots', timestamp0)
    d  blobstorage

Let's try that some more, with a new batch of mock Data.fs backups and extra blob files.
Then we can more easily test restoring to a specific time later.
Note that due to the timestamps no renaming takes place from blobstorage.0 to blobstorage.1.
We sleep a bit, because I sometimes get slightly different test results.

    >>> import time
    >>> time.sleep(1)
    >>> write('var', 'snapshotbackups', '1999-12-31-01-02-03.fsz', 'mock datafs backup')
    >>> write('var', 'blobstorage', 'blob2.txt', 'Sample blob 2.')
    >>> print(system('bin/snapshotbackup'))
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/snapshotbackups
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots
    INFO: rsync -a  --delete --link-dest=../blobstorage.1999-12-31-01-01-03 /sample-buildout/var/blobstorage /sample-buildout/var/blobstoragesnapshots/blobstorage.1999-12-31-01-02-03
    INFO: Creating symlink from latest to blobstorage.1999-12-31-01-02-03
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/snapshotbackups -F --gzip
    >>> ls('var/blobstoragesnapshots')
    d  blobstorage.1999-12-31-01-01-03
    d  blobstorage.1999-12-31-01-02-03
    d  latest
    >>> timestamp1 = 'blobstorage.1999-12-31-01-02-03'
    >>> ls('var', 'blobstoragesnapshots', timestamp1, 'blobstorage')
    -  blob1.txt
    -  blob2.txt
    >>> ls('var', 'blobstoragesnapshots', timestamp0, 'blobstorage')
    -  blob1.txt
    >>> cat('var', 'blobstoragesnapshots', timestamp1, 'blobstorage', 'blob1.txt')
    Sample blob 1.
    >>> cat('var', 'blobstoragesnapshots', timestamp1, 'blobstorage', 'blob2.txt')
    Sample blob 2.
    >>> cat('var', 'blobstoragesnapshots', timestamp0, 'blobstorage', 'blob1.txt')
    Sample blob 1.

Now remove an item and change an item.
Actually, files in blobstorage are not expected to change ever.
But let's test it for good measure::

    >>> time.sleep(1)
    >>> write('var', 'snapshotbackups', '1999-12-31-01-03-03.fsz', 'mock datafs backup')
    >>> remove('var', 'blobstorage', 'blob2.txt')
    >>> write('var', 'blobstorage', 'blob1.txt', 'Sample blob 1 version 2.')
    >>> print(system('bin/snapshotbackup'))
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/snapshotbackups
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots
    INFO: rsync -a  --delete --link-dest=../blobstorage.1999-12-31-01-02-03 /sample-buildout/var/blobstorage /sample-buildout/var/blobstoragesnapshots/blobstorage.1999-12-31-01-03-03
    INFO: Creating symlink from latest to blobstorage.1999-12-31-01-03-03
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/snapshotbackups -F --gzip
    >>> ls('var/blobstoragesnapshots')
    d  blobstorage.1999-12-31-01-01-03
    d  blobstorage.1999-12-31-01-02-03
    d  blobstorage.1999-12-31-01-03-03
    d  latest
    >>> timestamp2 = 'blobstorage.1999-12-31-01-03-03'
    >>> ls('var', 'blobstoragesnapshots', timestamp2, 'blobstorage')
    -  blob1.txt
    >>> ls('var', 'blobstoragesnapshots', timestamp1, 'blobstorage')
    -  blob1.txt
    -  blob2.txt
    >>> ls('var', 'blobstoragesnapshots', timestamp0, 'blobstorage')
    -  blob1.txt
    >>> cat('var', 'blobstoragesnapshots', timestamp2, 'blobstorage', 'blob1.txt')
    Sample blob 1 version 2.
    >>> cat('var', 'blobstoragesnapshots', timestamp1, 'blobstorage', 'blob1.txt')
    Sample blob 1.
    >>> cat('var', 'blobstoragesnapshots', timestamp0, 'blobstorage', 'blob1.txt')
    Sample blob 1.

Let's check the inodes of two files, to see if they are the same.  Not
sure if this works on all operating systems.

    >>> stat_0 = os.stat('var/blobstoragesnapshots/{0}/blobstorage/blob1.txt'.format(timestamp0))
    >>> stat_1 = os.stat('var/blobstoragesnapshots/{0}/blobstorage/blob1.txt'.format(timestamp1))
    >>> stat_0.st_ino == stat_1.st_ino
    True

Let's see how a bin/backup goes.
Again mock some repozo backups with timestamps.

    >>> time.sleep(1)
    >>> mkdir('var', 'backups')
    >>> write('var', 'backups', '1999-12-31-02-01-03.fsz', 'mock datafs backup')
    >>> print(system('bin/backup'))
    INFO: Created /sample-buildout/var/blobstoragebackups
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/backups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups
    INFO: rsync -a  /sample-buildout/var/blobstorage /sample-buildout/var/blobstoragebackups/blobstorage.1999-12-31-02-01-03
    INFO: Creating symlink from latest to blobstorage.1999-12-31-02-01-03
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups --quick --gzip
    >>> backup_timestamp0 = 'blobstorage.1999-12-31-02-01-03'
    >>> ls('var', 'blobstoragebackups')
    d  blobstorage.1999-12-31-02-01-03
    d  latest
    >>> ls('var', 'blobstoragebackups', backup_timestamp0)
    d  blobstorage
    >>> ls('var', 'blobstoragebackups', backup_timestamp0, 'blobstorage')
    -  blob1.txt

We try again with an extra 'blob' and a changed 'blob', and a new filestorage backup:

    >>> time.sleep(1)
    >>> write('var', 'backups', '1999-12-31-02-02-03.fsz', 'mock datafs backup')
    >>> write('var', 'blobstorage', 'blob2.txt', 'Sample blob 2.')
    >>> write('var', 'blobstorage', 'blob1.txt', 'Sample blob 1 version 3.')
    >>> print(system('bin/backup'))
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/backups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups
    INFO: rsync -a  --delete --link-dest=../blobstorage.1999-12-31-02-01-03 /sample-buildout/var/blobstorage /sample-buildout/var/blobstoragebackups/blobstorage.1999-12-31-02-02-03
    INFO: Creating symlink from latest to blobstorage.1999-12-31-02-02-03
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups --quick --gzip
    >>> ls('var', 'blobstoragebackups')
    d  blobstorage.1999-12-31-02-01-03
    d  blobstorage.1999-12-31-02-02-03
    d  latest
    >>> backup_timestamp1 = 'blobstorage.1999-12-31-02-02-03'
    >>> ls('var', 'blobstoragebackups', backup_timestamp1, 'blobstorage')
    -  blob1.txt
    -  blob2.txt
    >>> ls('var', 'blobstoragebackups', backup_timestamp0, 'blobstorage')
    -  blob1.txt
    >>> cat('var', 'blobstoragebackups', backup_timestamp1, 'blobstorage', 'blob1.txt')
    Sample blob 1 version 3.
    >>> cat('var', 'blobstoragebackups', backup_timestamp0, 'blobstorage', 'blob1.txt')
    Sample blob 1 version 2.

Write a third file.

    >>> write('var', 'blobstorage', 'blob3.txt', 'Sample blob 3.')
    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt
    -  blob3.txt

Now try a restore.
The third file should be gone afterwards::

    >>> print(system('bin/restore', input='no\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Not restoring.
    <BLANKLINE>
    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt
    -  blob3.txt
    >>> print(system('bin/restore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-buildout/var/backups to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups/blobstorage.1999-12-31-02-02-03/blobstorage /sample-buildout/var
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups
    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt
    >>> cat('var', 'blobstorage', 'blob1.txt')
    Sample blob 1 version 3.

With the ``no-prompt`` option we avoid the question::

    >>> write('var', 'blobstorage', 'blob3.txt', 'Sample blob 3.')
    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt
    -  blob3.txt
    >>> print(system('bin/restore --no-prompt'))
    <BLANKLINE>
    INFO: Please wait while restoring database file: /sample-buildout/var/backups to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups/blobstorage.1999-12-31-02-02-03/blobstorage /sample-buildout/var
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups
    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt
    >>> cat('var', 'blobstorage', 'blob1.txt')
    Sample blob 1 version 3.

Since release 2.3 we can also restore blobs to a specific date/time.
Since we use timestamps, this should be fairly straight forward.

    >>> backup_timestamp0 < backup_timestamp1
    True
    >>> backup_timestamp0
    'blobstorage.1999-12-31-02-01-03'
    >>> print(system('bin/restore 1999-12-31-02-01-03', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Date restriction: restoring state at ...
    INFO: Please wait while restoring database file: /sample-buildout/var/backups to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups/blobstorage.1999-12-31-02-01-03/blobstorage /sample-buildout/var
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups -D ...

The second blob file is now no longer in the blob storage.

    >>> ls('var/blobstorage')
    -  blob1.txt

The first blob file is back to an earlier version::

    >>> cat('var', 'blobstorage', 'blob1.txt')
    Sample blob 1 version 2.

The snapshotrestore works too::

    >>> print(system('bin/snapshotrestore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-buildout/var/snapshotbackups to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/blobstoragesnapshots to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragesnapshots/blobstorage.1999-12-31-01-03-03/blobstorage /sample-buildout/var
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/snapshotbackups

Check that this fits what is in the most recent snapshot::

    >>> ls('var/blobstorage')
    -  blob1.txt
    >>> ls('var/blobstoragesnapshots')
    d  blobstorage.1999-12-31-01-01-03
    d  blobstorage.1999-12-31-01-02-03
    d  blobstorage.1999-12-31-01-03-03
    d  latest
    >>> ls('var', 'blobstoragesnapshots', timestamp2, 'blobstorage')
    -  blob1.txt
    >>> ls('var', 'blobstoragesnapshots', timestamp1, 'blobstorage')
    -  blob1.txt
    -  blob2.txt
    >>> ls('var', 'blobstoragesnapshots', timestamp0, 'blobstorage')
    -  blob1.txt
    >>> cat('var', 'blobstoragesnapshots', timestamp2, 'blobstorage', 'blob1.txt')
    Sample blob 1 version 2.
    >>> cat('var', 'blobstoragesnapshots', timestamp1, 'blobstorage', 'blob1.txt')
    Sample blob 1.
    >>> cat('var', 'blobstoragesnapshots', timestamp0, 'blobstorage', 'blob1.txt')
    Sample blob 1.
    >>> cat('var', 'blobstorage', 'blob1.txt')
    Sample blob 1 version 2.

Since release 2.3 we can also restore blob snapshots to a specific date/time.

Since we use timestamps, this should be fairly straight forward.

    >>> timestamp0 < timestamp1 < timestamp2
    True
    >>> timestamp1
    'blobstorage.1999-12-31-01-02-03'
    >>> print(system('bin/snapshotrestore 1999-12-31-01-02-03', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Date restriction: restoring state at ...
    INFO: Please wait while restoring database file: /sample-buildout/var/snapshotbackups to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/blobstoragesnapshots to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragesnapshots/blobstorage.1999-12-31-01-02-03/blobstorage /sample-buildout/var
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/snapshotbackups -D 1999-12-31-01-02-03

The second blob file was only in blobstorage snapshot number 1 when we
started and now it is also in the main blobstorage again.

    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt
    >>> cat('var', 'blobstorage', 'blob1.txt')
    Sample blob 1.
