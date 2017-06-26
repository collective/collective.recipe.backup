# -*-doctest-*-

No rsync
========

Just to isolate some test differences, we run an empty buildout once::

    >>> ignore = system(buildout)

Add mock ``bin/repozo`` script::

    >>> import sys
    >>> write('bin', 'repozo',
    ...       "#!%s\nimport sys\nprint ' '.join(sys.argv[1:])" % sys.executable)
    >>> dontcare = system('chmod u+x bin/repozo')

If you cannot use rsync and hard links (which may not work on Windows)
you can set ``use_rsync = false``.  Then we will do a simple copy.

First we create some fresh content:

    >>> mkdir('var')
    >>> mkdir('var/blobstorage')
    >>> write('var', 'blobstorage', 'blob1.txt', "Sample blob 1.")
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

    >>> print system(buildout)
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
    >>> print output
    INFO: Created /sample-buildout/var/blobstoragebackups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups
    INFO: Copying /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups/blobstorage.0/blobstorage
    <BLANKLINE>

Try again to see that renaming/rotating keeps working::

    >>> output = system('bin/backup')
    >>> 'rsync' in output
    False
    >>> print output
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups
    INFO: Renaming blobstorage.0 to blobstorage.1.
    INFO: Copying /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups/blobstorage.0/blobstorage
    <BLANKLINE>

And again to see that for incremental backups no old blob backups are removed::

    >>> output = system('bin/backup')
    >>> 'rsync' in output
    False
    >>> print output
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups
    INFO: Renaming blobstorage.1 to blobstorage.2.
    INFO: Renaming blobstorage.0 to blobstorage.1.
    INFO: Copying /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups/blobstorage.0/blobstorage
    <BLANKLINE>

Now a restore::

    >>> output = system('bin/restore', input='yes\n')
    >>> 'rsync' in output
    False
    >>> print output
    <BLANKLINE>
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups to /sample-buildout/var/blobstorage
    INFO: Removing /sample-buildout/var/blobstorage
    INFO: Copying /sample-buildout/var/blobstoragebackups/blobstorage.0/blobstorage to /sample-buildout/var/blobstorage
    <BLANKLINE>

Snapshots should work too::

    >>> output = system('bin/snapshotbackup')
    >>> 'rsync' in output
    False
    >>> print output
    INFO: Created /sample-buildout/var/blobstoragesnapshots
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots
    INFO: Copying /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots/blobstorage.0/blobstorage
    <BLANKLINE>

Try again to see that renaming/rotating keeps working::

    >>> output = system('bin/snapshotbackup')
    >>> 'rsync' in output
    False
    >>> print output
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots
    INFO: Renaming blobstorage.0 to blobstorage.1.
    INFO: Copying /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots/blobstorage.0/blobstorage
    <BLANKLINE>

And again to see that removing old backups works::

    >>> output = system('bin/snapshotbackup')
    >>> 'rsync' in output
    False
    >>> print output
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots
    INFO: Renaming blobstorage.1 to blobstorage.2.
    INFO: Renaming blobstorage.0 to blobstorage.1.
    INFO: Copying /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots/blobstorage.0/blobstorage
    INFO: Removed 1 blob backup(s), the latest 2 backup(s) have been kept.
    <BLANKLINE>

And the snapshotrestore::

    >>> output = system('bin/snapshotrestore', input='yes\n')
    >>> 'rsync' in output
    False
    >>> print output
    <BLANKLINE>
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Restoring blobs from /sample-buildout/var/blobstoragesnapshots to /sample-buildout/var/blobstorage
    INFO: Removing /sample-buildout/var/blobstorage
    INFO: Copying /sample-buildout/var/blobstoragesnapshots/blobstorage.0/blobstorage to /sample-buildout/var/blobstorage
    <BLANKLINE>
