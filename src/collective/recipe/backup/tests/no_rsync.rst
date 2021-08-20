# -*-doctest-*-

No rsync
========

If you cannot use rsync and hard links (which may not work on Windows)
you can set ``use_rsync = false``.  Then we will do a simple copy.

First we create some fresh content:

    >>> mkdir('var/blobstorage')
    >>> write('var', 'blobstorage', 'blob1.txt', 'Sample blob 1.')
    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... only_blobs = true
    ... use_rsync = false
    ... """)

One thing we test here is if the buildout does not create too many
directories that will not get used because have set only_blobs=true::

    >>> print(system(buildout))
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    <BLANKLINE>

Check the output of bin/backup and explicitly test that rsync is
nowhere to be found::

    >>> output = system('bin/backup')
    >>> 'rsync' in output
    False
    >>> print(output)
    INFO: Created /sample-buildout/var/blobstoragebackups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups
    INFO: Copying /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups/blobstorage.20.../blobstorage
    INFO: Creating symlink from latest to blobstorage.20...
    <BLANKLINE>

Try again. but sleep 1 second so we are sure the timestamp gets a new name:

    >>> import time
    >>> time.sleep(1)
    >>> output = system('bin/backup')
    >>> 'rsync' in output
    False
    >>> print(output)
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups
    INFO: Copying /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups/blobstorage.20.../blobstorage
    INFO: Creating symlink from latest to blobstorage.20...
    <BLANKLINE>
    >>> ls('var', 'blobstoragebackups')
    d  blobstorage.20...
    d  blobstorage.20...
    d  latest

And again to see that for incremental backups no old blob backups are removed::

    >>> time.sleep(1)
    >>> output = system('bin/backup')
    >>> 'rsync' in output
    False
    >>> print(output)
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups
    INFO: Copying /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups/blobstorage.20.../blobstorage
    INFO: Creating symlink from latest to blobstorage.20...
    <BLANKLINE>
    >>> ls('var', 'blobstoragebackups')
    d  blobstorage.20...
    d  blobstorage.20...
    d  blobstorage.20...
    d  latest

Now a restore::

    >>> output = system('bin/restore', input='yes\n')
    >>> 'rsync' in output
    False
    >>> print(output)
    <BLANKLINE>
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups to /sample-buildout/var/blobstorage
    INFO: Removing /sample-buildout/var/blobstorage
    INFO: Copying /sample-buildout/var/blobstoragebackups/blobstorage.20.../blobstorage to /sample-buildout/var/blobstorage
    <BLANKLINE>

Snapshots should work too::

    >>> output = system('bin/snapshotbackup')
    >>> 'rsync' in output
    False
    >>> print(output)
    INFO: Created /sample-buildout/var/blobstoragesnapshots
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots
    INFO: Copying /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots/blobstorage.20.../blobstorage
    INFO: Creating symlink from latest to blobstorage.20...
    <BLANKLINE>

Try again:

    >>> time.sleep(1)
    >>> output = system('bin/snapshotbackup')
    >>> 'rsync' in output
    False
    >>> print(output)
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots
    INFO: Copying /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots/blobstorage.20.../blobstorage
    INFO: Creating symlink from latest to blobstorage.20...
    <BLANKLINE>
    >>> ls('var', 'blobstoragesnapshots')
    d  blobstorage.20...
    d  blobstorage.20...
    d  latest

And again to see that removing old backups works::

    >>> time.sleep(1)
    >>> output = system('bin/snapshotbackup')
    >>> 'rsync' in output
    False
    >>> print(output)
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots
    INFO: Copying /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots/blobstorage.20.../blobstorage
    INFO: Creating symlink from latest to blobstorage.20...
    INFO: Removed 1 blob backup, the latest 2 backups have been kept.
    <BLANKLINE>
    >>> ls('var', 'blobstoragesnapshots')
    d  blobstorage.20...
    d  blobstorage.20...
    d  latest

And the snapshotrestore::

    >>> output = system('bin/snapshotrestore', input='yes\n')
    >>> 'rsync' in output
    False
    >>> print(output)
    <BLANKLINE>
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Restoring blobs from /sample-buildout/var/blobstoragesnapshots to /sample-buildout/var/blobstorage
    INFO: Removing /sample-buildout/var/blobstorage
    INFO: Copying /sample-buildout/var/blobstoragesnapshots/blobstorage.20.../blobstorage to /sample-buildout/var/blobstorage
    <BLANKLINE>
