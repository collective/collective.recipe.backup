# -*-doctest-*-

Incremental blob backups
========================

Incremental blob backups requires the blob_timestamps option, and automatically turns it on.
This started as a copy of the ``blob_timestamps.rst`` file.
Several corner cases are only tested in that file, not in the current one.

Some imports:

    >>> import os

Write a buildout config.
We start with a wrong one, which explicitly sets blob_timestamps to false::

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
    ... archive_blob = true
    ... blob_timestamps = false
    ... incremental_blobs = true
    ... keep = 3
    ... """)
    >>> print(system(buildout))
    While:
      Installing.
      Getting section backup.
      Initializing section backup.
    Error: Cannot have blob_timestamps false and incremental_blobs true.

So leave the blob_timestamps option out::

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
    ... archive_blob = true
    ... incremental_blobs = true
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

Test the snapshotbackup first, as that should be easiest.
It is useless to use incremental blobs here: a snapshot is always one tarball.

    >>> print(system('bin/snapshotbackup'))
    INFO: Created /sample-buildout/var/snapshotbackups
    INFO: Created /sample-buildout/var/blobstoragesnapshots
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/snapshotbackups
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots
    INFO: tar cf /sample-buildout/var/blobstoragesnapshots/blobstorage.20...-...-...-...-...-....tar  -C /sample-buildout/var/blobstorage .
    INFO: Creating symlink from latest to blobstorage.20...-...-...-...-...-....tar
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/snapshotbackups -F --gzip
    >>> ls('var', 'blobstoragesnapshots')
    -  blobstorage.20...-...-...-...-...-....tar
    l  latest
    >>> len(os.listdir('var/blobstoragesnapshots'))
    2
    >>> print(os.path.realpath('var/blobstoragesnapshots/latest'))
    /sample-buildout/var/blobstoragesnapshots/blobstorage.20...-...-...-...-...-....tar

We mock a file storage backup from 2016:

    >>> mkdir('var', 'backups')
    >>> write('var', 'backups', '2016-12-25-00-00-00.fsz', 'mock fs backup')

Now let's see how a bin/backup goes:

    >>> print(system('bin/backup'))
    INFO: Created /sample-buildout/var/blobstoragebackups
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/backups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups
    INFO: tar cf /sample-buildout/var/blobstoragebackups/blobstorage.2016-12-25-00-00-00.tar --listed-incremental='/sample-buildout/var/blobstoragebackups/blobstorage.2016-12-25-00-00-00.snar' -C /sample-buildout/var/blobstorage .
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups --quick --gzip
    >>> ls('var', 'blobstoragebackups')
    -  blobstorage.2016-12-25-00-00-00.snar
    -  blobstorage.2016-12-25-00-00-00.tar

We try again with an extra 'blob' and a changed 'blob'.
It helps if we wait a bit.

    >>> import time
    >>> time.sleep(1)
    >>> write('var', 'blobstorage', 'blob2.txt', 'Sample blob 2.')
    >>> write('var', 'blobstorage', 'blob1.txt', 'Sample blob 1 version 2.')
    >>> write('var', 'backups', '2016-12-26-00-00-00.deltafsz', 'mock fs backup')
    >>> print(system('bin/backup'))
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/backups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups
    INFO: tar cf /sample-buildout/var/blobstoragebackups/blobstorage.2016-12-26-00-00-00.delta.tar --listed-incremental='/sample-buildout/var/blobstoragebackups/blobstorage.2016-12-25-00-00-00.snar'  -C /sample-buildout/var/blobstorage .
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups --quick --gzip
    >>> ls('var', 'blobstoragebackups')
    -  blobstorage.2016-12-25-00-00-00.snar
    -  blobstorage.2016-12-25-00-00-00.tar
    -  blobstorage.2016-12-26-00-00-00.delta.tar

Write a third file and change the first again.

    >>> time.sleep(1)
    >>> write('var', 'blobstorage', 'blob3.txt', 'Sample blob 3.')
    >>> write('var', 'blobstorage', 'blob1.txt', 'Sample blob 1 version 3.')
    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt
    -  blob3.txt

Now try a restore.
The third file should be gone afterwards, and the first file reverted to the second version::

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
    INFO: Removing /sample-buildout/var/blobstorage
    INFO: Found 2 incremental backups to restore.
    INFO: Extracting /sample-buildout/var/blobstoragebackups/blobstorage.2016-12-25-00-00-00.tar to /sample-buildout/var/blobstorage
    INFO: tar xf /sample-buildout/var/blobstoragebackups/blobstorage.2016-12-25-00-00-00.tar --incremental -C /sample-buildout/var/blobstorage
    INFO: Extracting /sample-buildout/var/blobstoragebackups/blobstorage.2016-12-26-00-00-00.delta.tar to /sample-buildout/var/blobstorage
    INFO: tar xf /sample-buildout/var/blobstoragebackups/blobstorage.2016-12-26-00-00-00.delta.tar --incremental -C /sample-buildout/var/blobstorage
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups
    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt
    >>> cat('var', 'blobstorage', 'blob1.txt')
    Sample blob 1 version 2.

Since release 2.3 we can also restore blobs to a specific date/time.
Since we use timestamps, this should be fairly straight forward.

    >>> time_string = '2016-12-25-00-00-00'
    >>> print(system('bin/restore %s' % time_string, input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Date restriction: restoring state at ...
    INFO: Please wait while restoring database file: /sample-buildout/var/backups to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups to /sample-buildout/var/blobstorage
    INFO: Removing /sample-buildout/var/blobstorage
    INFO: Extracting /sample-buildout/var/blobstoragebackups/blobstorage.2016-12-25-00-00-00.tar to /sample-buildout/var/blobstorage
    INFO: tar xf /sample-buildout/var/blobstoragebackups/blobstorage.2016-12-25-00-00-00.tar -C /sample-buildout/var/blobstorage
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups -D ...

The second blob file is now no longer in the blob storage.

    >>> ls('var/blobstorage')
    -  blob1.txt

The first blob file is back to an earlier version::

    >>> cat('var', 'blobstorage', 'blob1.txt')
    Sample blob 1.
