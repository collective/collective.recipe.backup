# -*-doctest-*-

With or without gzip
====================

Just to isolate some test differences, we run an empty buildout once::

    >>> ignore = system(buildout)

Add mock ``bin/repozo`` script::

    >>> import sys
    >>> write('bin', 'repozo',
    ...       "#!%s\nimport sys\nprint ' '.join(sys.argv[1:])" % sys.executable)
    >>> dontcare = system('chmod u+x bin/repozo')

Create directories and content::

    >>> mkdir('var')
    >>> mkdir('var', 'blobstorage')
    >>> write('var', 'blobstorage', 'blob1.txt', "Sample blob 1.")

Create some archived (gzipped) and not-archived separate backup scripts::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = nozipbackup zippedbackup
    ...
    ... [nozipbackup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... backup_blobs = true
    ... gzip = false
    ... gzip_blob = false
    ...
    ... [zippedbackup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... backup_blobs = true
    ... gzip = true
    ... gzip_blob = true
    ... """)
    >>> print system(buildout)
    Installing nozipbackup.
    Generated script '/sample-buildout/bin/nozipbackup'.
    Generated script '/sample-buildout/bin/nozipbackup-full'.
    Generated script '/sample-buildout/bin/nozipbackup-snapshot'.
    Generated script '/sample-buildout/bin/nozipbackup-restore'.
    Generated script '/sample-buildout/bin/nozipbackup-snapshotrestore'.
    Installing zippedbackup.
    Generated script '/sample-buildout/bin/zippedbackup'.
    Generated script '/sample-buildout/bin/zippedbackup-full'.
    Generated script '/sample-buildout/bin/zippedbackup-snapshot'.
    Generated script '/sample-buildout/bin/zippedbackup-restore'.
    Generated script '/sample-buildout/bin/zippedbackup-snapshotrestore'.
    <BLANKLINE>

Now we test it.  First the `normal` backup.  The nozipbackup backs up without
using archiving technology::

    >>> print system('bin/nozipbackup')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/nozipbackups --quick
    INFO: Created /sample-buildout/var/nozipbackups
    INFO: Created /sample-buildout/var/nozipbackup-blobstorages
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/nozipbackups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/nozipbackup-blobstorages
    INFO: rsync -a  /sample-buildout/var/blobstorage /sample-buildout/var/nozipbackup-blobstorages/blobstorage.0
    <BLANKLINE>
    >>> print system('bin/nozipbackup-snapshot')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/nozipbackup-snapshots -F
    INFO: Created /sample-buildout/var/nozipbackup-snapshots
    INFO: Created /sample-buildout/var/nozipbackup-blobstoragesnapshots
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/nozipbackup-snapshots
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/nozipbackup-blobstoragesnapshots
    INFO: rsync -a  /sample-buildout/var/blobstorage /sample-buildout/var/nozipbackup-blobstoragesnapshots/blobstorage.0
    <BLANKLINE>

And zippedbackup backs up by archiving backup::

    >>> print system('bin/zippedbackup')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/zippedbackups --quick --gzip
    INFO: Created /sample-buildout/var/zippedbackups
    INFO: Created /sample-buildout/var/zippedbackup-blobstorages
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/zippedbackups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/zippedbackup-blobstorages
    INFO: tar czf /sample-buildout/var/zippedbackup-blobstorages/blobstorage.0.tar.gz -C /sample-buildout/var/blobstorage .
    <BLANKLINE>
    >>> print system('bin/zippedbackup-snapshot')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/zippedbackup-snapshots -F --gzip
    INFO: Created /sample-buildout/var/zippedbackup-snapshots
    INFO: Created /sample-buildout/var/zippedbackup-blobstoragesnapshots
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/zippedbackup-snapshots
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/zippedbackup-blobstoragesnapshots
    INFO: tar czf /sample-buildout/var/zippedbackup-blobstoragesnapshots/blobstorage.0.tar.gz -C /sample-buildout/var/blobstorage .

    <BLANKLINE>

Now test the restore::

    >>> print system('bin/nozipbackup-restore', input='yes\n')
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/nozipbackups
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
    >>> print system('bin/nozipbackup-snapshotrestore', input='yes\n')
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/nozipbackup-snapshots
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)? INFO: Please wait while restoring database file: /sample-buildout/var/nozipbackup-snapshots to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/nozipbackup-blobstoragesnapshots to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/var/nozipbackup-blobstoragesnapshots/blobstorage.0/blobstorage /sample-buildout/var
    <BLANKLINE>
    >>> print system('bin/zippedbackup-restore', input='yes\n')
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/zippedbackups
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)? INFO: Please wait while restoring database file: /sample-buildout/var/zippedbackups to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/zippedbackup-blobstorages to /sample-buildout/var/blobstorage
    INFO: Removing /sample-buildout/var/blobstorage
    INFO: Extracting /sample-buildout/var/zippedbackup-blobstorages/blobstorage.0.tar.gz to /sample-buildout/var/blobstorage
    INFO: tar xzf /sample-buildout/var/zippedbackup-blobstorages/blobstorage.0.tar.gz -C /sample-buildout/var/blobstorage
    <BLANKLINE>
    >>> print system('bin/zippedbackup-snapshotrestore', input='yes\n')
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/zippedbackup-snapshots
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)? INFO: Please wait while restoring database file: /sample-buildout/var/zippedbackup-snapshots to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/zippedbackup-blobstoragesnapshots to /sample-buildout/var/blobstorage
    INFO: Removing /sample-buildout/var/blobstorage
    INFO: Extracting /sample-buildout/var/zippedbackup-blobstoragesnapshots/blobstorage.0.tar.gz to /sample-buildout/var/blobstorage
    INFO: tar xzf /sample-buildout/var/zippedbackup-blobstoragesnapshots/blobstorage.0.tar.gz -C /sample-buildout/var/blobstorage
    <BLANKLINE>
