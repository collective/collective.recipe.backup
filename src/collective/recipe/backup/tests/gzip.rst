# -*-doctest-*-

With or without gzip
====================

Create directories and content::

    >>> mkdir('var', 'blobstorage')
    >>> write('var', 'blobstorage', 'blob1.txt', "Sample blob 1.")

Create some archived (gzipped) and not-archived separate backup scripts::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = nozipbackup zippedbackup compressedbackup
    ...
    ... [nozipbackup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... backup_blobs = true
    ... gzip = false
    ... archive_blob = false
    ...
    ... [zippedbackup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... backup_blobs = true
    ... gzip = true
    ... archive_blob = true
    ...
    ... [compressedbackup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... backup_blobs = true
    ... gzip = true
    ... archive_blob = true
    ... compress_blob = true
    ... """)
    >>> print(system(buildout))
    Installing nozipbackup.
    Generated script '/sample-buildout/bin/nozipbackup'.
    Generated script '/sample-buildout/bin/nozipbackup-snapshot'.
    Generated script '/sample-buildout/bin/nozipbackup-restore'.
    Generated script '/sample-buildout/bin/nozipbackup-snapshotrestore'.
    Installing zippedbackup.
    Generated script '/sample-buildout/bin/zippedbackup'.
    Generated script '/sample-buildout/bin/zippedbackup-snapshot'.
    Generated script '/sample-buildout/bin/zippedbackup-restore'.
    Generated script '/sample-buildout/bin/zippedbackup-snapshotrestore'.
    Installing compressedbackup.
    Generated script '/sample-buildout/bin/compressedbackup'.
    Generated script '/sample-buildout/bin/compressedbackup-snapshot'.
    Generated script '/sample-buildout/bin/compressedbackup-restore'.
    Generated script '/sample-buildout/bin/compressedbackup-snapshotrestore'.
    <BLANKLINE>

Now we test it.  First the `normal` backup.  The nozipbackup backs up without
using archiving technology::

    >>> print(system('bin/nozipbackup'))
    INFO: Created /sample-buildout/var/nozipbackups
    INFO: Created /sample-buildout/var/nozipbackup-blobstorages
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/nozipbackups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/nozipbackup-blobstorages
    INFO: rsync -a  /sample-buildout/var/blobstorage /sample-buildout/var/nozipbackup-blobstorages/blobstorage.0
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/nozipbackups --quick
    >>> print(system('bin/nozipbackup-snapshot'))
    INFO: Created /sample-buildout/var/nozipbackup-snapshots
    INFO: Created /sample-buildout/var/nozipbackup-blobstoragesnapshots
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/nozipbackup-snapshots
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/nozipbackup-blobstoragesnapshots
    INFO: rsync -a  /sample-buildout/var/blobstorage /sample-buildout/var/nozipbackup-blobstoragesnapshots/blobstorage.0
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/nozipbackup-snapshots -F

zippedbackup backs up by gzipping the filestorage backup and archiving the blob backup with tar::

    >>> print(system('bin/zippedbackup'))
    INFO: Created /sample-buildout/var/zippedbackups
    INFO: Created /sample-buildout/var/zippedbackup-blobstorages
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/zippedbackups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/zippedbackup-blobstorages
    INFO: tar cf /sample-buildout/var/zippedbackup-blobstorages/blobstorage.0.tar -C /sample-buildout/var/blobstorage .
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/zippedbackups --quick --gzip
    >>> print(system('bin/zippedbackup-snapshot'))
    INFO: Created /sample-buildout/var/zippedbackup-snapshots
    INFO: Created /sample-buildout/var/zippedbackup-blobstoragesnapshots
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/zippedbackup-snapshots
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/zippedbackup-blobstoragesnapshots
    INFO: tar cf /sample-buildout/var/zippedbackup-blobstoragesnapshots/blobstorage.0.tar -C /sample-buildout/var/blobstorage .

    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/zippedbackup-snapshots -F --gzip

And compressedbackup compresses the blob archive::

    >>> print(system('bin/compressedbackup'))
    INFO: Created /sample-buildout/var/compressedbackups
    INFO: Created /sample-buildout/var/compressedbackup-blobstorages
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/compressedbackups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/compressedbackup-blobstorages
    INFO: tar czf /sample-buildout/var/compressedbackup-blobstorages/blobstorage.0.tar.gz -C /sample-buildout/var/blobstorage .
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/compressedbackups --quick --gzip
    >>> print(system('bin/compressedbackup-snapshot'))
    INFO: Created /sample-buildout/var/compressedbackup-snapshots
    INFO: Created /sample-buildout/var/compressedbackup-blobstoragesnapshots
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/compressedbackup-snapshots
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/compressedbackup-blobstoragesnapshots
    INFO: tar czf /sample-buildout/var/compressedbackup-blobstoragesnapshots/blobstorage.0.tar.gz -C /sample-buildout/var/blobstorage .

    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/compressedbackup-snapshots -F --gzip

Now test the restore::

    >>> print(system('bin/nozipbackup-restore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Created directory /sample-buildout/var/filestorage
    INFO: Please wait while restoring database file: /sample-buildout/var/nozipbackups to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/nozipbackup-blobstorages to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/var/nozipbackup-blobstorages/blobstorage.0/blobstorage /sample-buildout/var
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/nozipbackups
    >>> print(system('bin/nozipbackup-snapshotrestore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)? INFO: Please wait while restoring database file: /sample-buildout/var/nozipbackup-snapshots to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/nozipbackup-blobstoragesnapshots to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/var/nozipbackup-blobstoragesnapshots/blobstorage.0/blobstorage /sample-buildout/var
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/nozipbackup-snapshots
    >>> print(system('bin/zippedbackup-restore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)? INFO: Please wait while restoring database file: /sample-buildout/var/zippedbackups to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/zippedbackup-blobstorages to /sample-buildout/var/blobstorage
    INFO: Removing /sample-buildout/var/blobstorage
    INFO: Extracting /sample-buildout/var/zippedbackup-blobstorages/blobstorage.0.tar to /sample-buildout/var/blobstorage
    INFO: tar xf /sample-buildout/var/zippedbackup-blobstorages/blobstorage.0.tar -C /sample-buildout/var/blobstorage
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/zippedbackups
    >>> print(system('bin/zippedbackup-snapshotrestore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)? INFO: Please wait while restoring database file: /sample-buildout/var/zippedbackup-snapshots to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/zippedbackup-blobstoragesnapshots to /sample-buildout/var/blobstorage
    INFO: Removing /sample-buildout/var/blobstorage
    INFO: Extracting /sample-buildout/var/zippedbackup-blobstoragesnapshots/blobstorage.0.tar to /sample-buildout/var/blobstorage
    INFO: tar xf /sample-buildout/var/zippedbackup-blobstoragesnapshots/blobstorage.0.tar -C /sample-buildout/var/blobstorage
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/zippedbackup-snapshots
    >>> print(system('bin/compressedbackup-restore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)? INFO: Please wait while restoring database file: /sample-buildout/var/compressedbackups to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/compressedbackup-blobstorages to /sample-buildout/var/blobstorage
    INFO: Removing /sample-buildout/var/blobstorage
    INFO: Extracting /sample-buildout/var/compressedbackup-blobstorages/blobstorage.0.tar.gz to /sample-buildout/var/blobstorage
    INFO: tar xzf /sample-buildout/var/compressedbackup-blobstorages/blobstorage.0.tar.gz -C /sample-buildout/var/blobstorage
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/compressedbackups
    >>> print(system('bin/compressedbackup-snapshotrestore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)? INFO: Please wait while restoring database file: /sample-buildout/var/compressedbackup-snapshots to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/compressedbackup-blobstoragesnapshots to /sample-buildout/var/blobstorage
    INFO: Removing /sample-buildout/var/blobstorage
    INFO: Extracting /sample-buildout/var/compressedbackup-blobstoragesnapshots/blobstorage.0.tar.gz to /sample-buildout/var/blobstorage
    INFO: tar xzf /sample-buildout/var/compressedbackup-blobstoragesnapshots/blobstorage.0.tar.gz -C /sample-buildout/var/blobstorage
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/compressedbackup-snapshots
