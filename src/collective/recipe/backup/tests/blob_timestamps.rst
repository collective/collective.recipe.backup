# -*-doctest-*-

Blob storage with timestamps
============================

These are tests with ``blob_timestamps = true``.
This started as a copy of the ``blobs.rst`` file.
Several corner cases are only tested in that file, not in the current one.

Just to isolate some test differences, we run an empty buildout once::

    >>> ignore = system(buildout)

Add mock ``bin/repozo`` script::

    >>> import os
    >>> import sys
    >>> write('bin', 'repozo',
    ...       "#!%s\nimport sys\nprint ' '.join(sys.argv[1:])" % sys.executable)
    >>> dontcare = system('chmod u+x bin/repozo')

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
    ... additional_filestorages =
    ...    foo ${buildout:directory}/var/filestorage/foo.fs ${buildout:directory}/var/blobstorage-foo
    ...    bar ${buildout:directory}/var/filestorage/bar.fs ${buildout:directory}/var/blobstorage-bar
    ... """)
    >>> print system(buildout)
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
    >>> mkdir('var')
    >>> mkdir('var', 'filestorage')
    >>> mkdir('var', 'blobstorage')
    >>> write('var', 'blobstorage', 'blob1.txt', "Sample blob 1.")
    >>> mkdir('var', 'blobstorage-foo')
    >>> write('var', 'blobstorage-foo', 'blob-foo1.txt', "Sample blob foo 1.")
    >>> mkdir('var', 'blobstorage-bar')
    >>> write('var', 'blobstorage-bar', 'blob-bar1.txt', "Sample blob bar 1.")

Test the snapshotbackup first, as that should be easiest.

    >>> print system('bin/snapshotbackup')
    --backup -f /sample-buildout/var/filestorage/foo.fs -r /sample-buildout/var/snapshotbackups_foo -F --gzip
    --backup -f /sample-buildout/var/filestorage/bar.fs -r /sample-buildout/var/snapshotbackups_bar -F --gzip
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/snapshotbackups -F --gzip
    INFO: Created /sample-buildout/var/snapshotbackups_foo
    INFO: Created /sample-buildout/var/blobstoragesnapshots_foo
    INFO: Created /sample-buildout/var/snapshotbackups_bar
    INFO: Created /sample-buildout/var/blobstoragesnapshots_bar
    INFO: Created /sample-buildout/var/snapshotbackups
    INFO: Created /sample-buildout/var/blobstoragesnapshots
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/foo.fs to /sample-buildout/var/snapshotbackups_foo
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/bar.fs to /sample-buildout/var/snapshotbackups_bar
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/snapshotbackups
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage-foo to /sample-buildout/var/blobstoragesnapshots_foo
    INFO: rsync -a  /sample-buildout/var/blobstorage-foo /sample-buildout/var/blobstoragesnapshots_foo/blobstorage-foo.20...
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage-bar to /sample-buildout/var/blobstoragesnapshots_bar
    INFO: rsync -a  /sample-buildout/var/blobstorage-bar /sample-buildout/var/blobstoragesnapshots_bar/blobstorage-bar.20...
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots
    INFO: rsync -a  /sample-buildout/var/blobstorage /sample-buildout/var/blobstoragesnapshots/blobstorage.20...-...-...-...-...-...
    <BLANKLINE>
    >>> ls('var', 'blobstoragesnapshots')
    d  blobstorage.20...-...-...-...-...-...
    >>> timestamp0 = os.listdir('var/blobstoragesnapshots/')[0]
    >>> ls('var', 'blobstoragesnapshots', timestamp0)
    d  blobstorage
    >>> ls('var', 'blobstoragesnapshots_foo')
    d  blobstorage-foo.20...-...-...-...-...-...
    >>> foo_timestamp0 = os.listdir('var/blobstoragesnapshots_foo/')[0]
    >>> ls('var', 'blobstoragesnapshots_foo', foo_timestamp0)
    d  blobstorage-foo
    >>> ls('var', 'blobstoragesnapshots_bar')
    d  blobstorage-bar.20...-...-...-...-...-...
    >>> bar_timestamp0 = os.listdir('var/blobstoragesnapshots_bar/')[0]
    >>> ls('var', 'blobstoragesnapshots_bar', bar_timestamp0)
    d  blobstorage-bar

Let's try that some more, with some time in between so we can more easily test restoring to a specific time later.
Note that due to the timestamps no renaming takes place from blobstorage.0 to blobstorage.1.

    >>> import time
    >>> time.sleep(2)
    >>> write('var', 'blobstorage', 'blob2.txt', "Sample blob 2.")
    >>> write('var', 'blobstorage-foo', 'blob-foo2.txt', "Sample blob foo 2.")
    >>> write('var', 'blobstorage-bar', 'blob-bar2.txt', "Sample blob bar 2.")
    >>> print system('bin/snapshotbackup')
    --backup -f /sample-buildout/var/filestorage/foo.fs -r /sample-buildout/var/snapshotbackups_foo -F --gzip
    --backup -f /sample-buildout/var/filestorage/bar.fs -r /sample-buildout/var/snapshotbackups_bar -F --gzip
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/snapshotbackups -F --gzip
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/foo.fs to /sample-buildout/var/snapshotbackups_foo
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/bar.fs to /sample-buildout/var/snapshotbackups_bar
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/snapshotbackups
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage-foo to /sample-buildout/var/blobstoragesnapshots_foo
    INFO: rsync -a  --delete --link-dest=../blobstorage-foo.20...-...-...-...-...-... /sample-buildout/var/blobstorage-foo /sample-buildout/var/blobstoragesnapshots_foo/blobstorage-foo.20...-...-...-...-...-...
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage-bar to /sample-buildout/var/blobstoragesnapshots_bar
    INFO: rsync -a  --delete --link-dest=../blobstorage-bar.20...-...-...-...-...-... /sample-buildout/var/blobstorage-bar /sample-buildout/var/blobstoragesnapshots_bar/blobstorage-bar.20...-...-...-...-...-...
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots
    INFO: rsync -a  --delete --link-dest=../blobstorage.20...-...-...-...-...-... /sample-buildout/var/blobstorage /sample-buildout/var/blobstoragesnapshots/blobstorage.20...-...-...-...-...-...
    <BLANKLINE>
    >>> ls('var/blobstoragesnapshots')
    d  blobstorage.20...-...-...-...-...-...
    d  blobstorage.20...-...-...-...-...-...
    >>> timestamp0 == os.listdir('var/blobstoragesnapshots/')[0]
    True
    >>> timestamp1 = os.listdir('var/blobstoragesnapshots/')[1]
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
    >>> ls('var', 'blobstoragesnapshots_foo')
    d  blobstorage-foo.20...-...-...-...-...-...
    d  blobstorage-foo.20...-...-...-...-...-...
    >>> foo_timestamp0 == os.listdir('var/blobstoragesnapshots_foo/')[0]
    True
    >>> foo_timestamp1 = os.listdir('var/blobstoragesnapshots_foo/')[1]
    >>> ls('var', 'blobstoragesnapshots_foo', foo_timestamp1, 'blobstorage-foo')
    -  blob-foo1.txt
    -  blob-foo2.txt
    >>> ls('var', 'blobstoragesnapshots_foo', foo_timestamp0, 'blobstorage-foo')
    -  blob-foo1.txt
    >>> cat('var', 'blobstoragesnapshots_foo', foo_timestamp1, 'blobstorage-foo', 'blob-foo1.txt')
    Sample blob foo 1.
    >>> cat('var', 'blobstoragesnapshots_foo', foo_timestamp1, 'blobstorage-foo', 'blob-foo2.txt')
    Sample blob foo 2.
    >>> cat('var', 'blobstoragesnapshots_foo', foo_timestamp0, 'blobstorage-foo', 'blob-foo1.txt')
    Sample blob foo 1.

Now remove an item and change an item.
Actually, files in blobstorage are not expected to change ever.
But let's test it for good measure::

    >>> time.sleep(2)
    >>> remove('var', 'blobstorage', 'blob2.txt')
    >>> remove('var', 'blobstorage-foo', 'blob-foo1.txt')
    >>> remove('var', 'blobstorage-bar', 'blob-bar1.txt')
    >>> write('var', 'blobstorage', 'blob1.txt', "Sample blob 1 version 2.")
    >>> print system('bin/snapshotbackup')
    --backup -f /sample-buildout/var/filestorage/foo.fs -r /sample-buildout/var/snapshotbackups_foo -F --gzip
    --backup -f /sample-buildout/var/filestorage/bar.fs -r /sample-buildout/var/snapshotbackups_bar -F --gzip
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/snapshotbackups -F --gzip
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/foo.fs to /sample-buildout/var/snapshotbackups_foo
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/bar.fs to /sample-buildout/var/snapshotbackups_bar
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/snapshotbackups
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage-foo to /sample-buildout/var/blobstoragesnapshots_foo
    INFO: rsync -a  --delete --link-dest=../blobstorage-foo.20...-...-...-...-...-... /sample-buildout/var/blobstorage-foo /sample-buildout/var/blobstoragesnapshots_foo/blobstorage-foo.20...-...-...-...-...-...
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage-bar to /sample-buildout/var/blobstoragesnapshots_bar
    INFO: rsync -a  --delete --link-dest=../blobstorage-bar.20...-...-...-...-...-... /sample-buildout/var/blobstorage-bar /sample-buildout/var/blobstoragesnapshots_bar/blobstorage-bar.20...-...-...-...-...-...
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots
    INFO: rsync -a  --delete --link-dest=../blobstorage.20...-...-...-...-...-... /sample-buildout/var/blobstorage /sample-buildout/var/blobstoragesnapshots/blobstorage.20...-...-...-...-...-...
    <BLANKLINE>
    >>> ls('var/blobstoragesnapshots')
    d  blobstorage.20...-...-...-...-...-...
    d  blobstorage.20...-...-...-...-...-...
    d  blobstorage.20...-...-...-...-...-...
    >>> timestamp0 == os.listdir('var/blobstoragesnapshots/')[0]
    True
    >>> timestamp1 == os.listdir('var/blobstoragesnapshots/')[1]
    True
    >>> timestamp2 = os.listdir('var/blobstoragesnapshots/')[2]
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
    >>> ls('var', 'blobstoragesnapshots_foo')
    d  blobstorage-foo.20...-...-...-...-...-...
    d  blobstorage-foo.20...-...-...-...-...-...
    d  blobstorage-foo.20...-...-...-...-...-...
    >>> foo_timestamp0 == os.listdir('var/blobstoragesnapshots_foo/')[0]
    True
    >>> foo_timestamp1 == os.listdir('var/blobstoragesnapshots_foo/')[1]
    True
    >>> foo_timestamp2 = os.listdir('var/blobstoragesnapshots_foo/')[2]
    >>> ls('var', 'blobstoragesnapshots_foo', foo_timestamp2, 'blobstorage-foo')
    -  blob-foo2.txt
    >>> ls('var', 'blobstoragesnapshots_foo', foo_timestamp1, 'blobstorage-foo')
    -  blob-foo1.txt
    -  blob-foo2.txt
    >>> ls('var', 'blobstoragesnapshots_foo', foo_timestamp0, 'blobstorage-foo')
    -  blob-foo1.txt

Let's check the inodes of two files, to see if they are the same.  Not
sure if this works on all operating systems.

    >>> stat_0 = os.stat('var/blobstoragesnapshots/{0}/blobstorage/blob1.txt'.format(timestamp0))
    >>> stat_1 = os.stat('var/blobstoragesnapshots/{0}/blobstorage/blob1.txt'.format(timestamp1))
    >>> stat_0.st_ino == stat_1.st_ino
    True

Let's see how a bin/backup goes:

    >>> print system('bin/backup')
    --backup -f /sample-buildout/var/filestorage/foo.fs -r /sample-buildout/var/backups_foo --quick --gzip
    --backup -f /sample-buildout/var/filestorage/bar.fs -r /sample-buildout/var/backups_bar --quick --gzip
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups --quick --gzip
    INFO: Created /sample-buildout/var/backups_foo
    INFO: Created /sample-buildout/var/blobstoragebackups_foo
    INFO: Created /sample-buildout/var/backups_bar
    INFO: Created /sample-buildout/var/blobstoragebackups_bar
    INFO: Created /sample-buildout/var/backups
    INFO: Created /sample-buildout/var/blobstoragebackups
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/foo.fs to /sample-buildout/var/backups_foo
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/bar.fs to /sample-buildout/var/backups_bar
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/backups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage-foo to /sample-buildout/var/blobstoragebackups_foo
    INFO: rsync -a  /sample-buildout/var/blobstorage-foo /sample-buildout/var/blobstoragebackups_foo/blobstorage-foo.20...-...-...-...-...-...
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage-bar to /sample-buildout/var/blobstoragebackups_bar
    INFO: rsync -a  /sample-buildout/var/blobstorage-bar /sample-buildout/var/blobstoragebackups_bar/blobstorage-bar.20...-...-...-...-...-...
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups
    INFO: rsync -a  /sample-buildout/var/blobstorage /sample-buildout/var/blobstoragebackups/blobstorage.20...-...-...-...-...-...
    <BLANKLINE>
    >>> backup_timestamp0 = os.listdir('var/blobstoragebackups/')[0]
    >>> ls('var', 'blobstoragebackups')
    d  blobstorage.20...-...-...-...-...-...
    >>> ls('var', 'blobstoragebackups', backup_timestamp0)
    d  blobstorage
    >>> ls('var', 'blobstoragebackups', backup_timestamp0, 'blobstorage')
    -  blob1.txt
    >>> foo_backup_timestamp0 = os.listdir('var/blobstoragebackups_foo/')[0]
    >>> ls('var', 'blobstoragebackups_foo')
    d  blobstorage-foo.20...-...-...-...-...-...
    >>> ls('var', 'blobstoragebackups_foo', foo_backup_timestamp0)
    d  blobstorage-foo
    >>> ls('var', 'blobstoragebackups_foo', foo_backup_timestamp0, 'blobstorage-foo')
    -  blob-foo2.txt

We try again with an extra 'blob' and a changed 'blob':

    >>> time.sleep(2)
    >>> write('var', 'blobstorage', 'blob2.txt', "Sample blob 2.")
    >>> write('var', 'blobstorage', 'blob1.txt', "Sample blob 1 version 3.")
    >>> print system('bin/backup')
    --backup -f /sample-buildout/var/filestorage/foo.fs -r /sample-buildout/var/backups_foo --quick --gzip
    --backup -f /sample-buildout/var/filestorage/bar.fs -r /sample-buildout/var/backups_bar --quick --gzip
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups --quick --gzip
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/foo.fs to /sample-buildout/var/backups_foo
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/bar.fs to /sample-buildout/var/backups_bar
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/backups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage-foo to /sample-buildout/var/blobstoragebackups_foo
    INFO: rsync -a  --delete --link-dest=../blobstorage-foo.20...-...-...-...-...-... /sample-buildout/var/blobstorage-foo /sample-buildout/var/blobstoragebackups_foo/blobstorage-foo.20...-...-...-...-...-...
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage-bar to /sample-buildout/var/blobstoragebackups_bar
    INFO: rsync -a  --delete --link-dest=../blobstorage-bar.20...-...-...-...-...-... /sample-buildout/var/blobstorage-bar /sample-buildout/var/blobstoragebackups_bar/blobstorage-bar.20...-...-...-...-...-...
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups
    INFO: rsync -a  --delete --link-dest=../blobstorage.20...-...-...-...-...-... /sample-buildout/var/blobstorage /sample-buildout/var/blobstoragebackups/blobstorage.20...-...-...-...-...-...
    <BLANKLINE>
    >>> ls('var', 'blobstoragebackups')
    d  blobstorage.20...-...-...-...-...-...
    d  blobstorage.20...-...-...-...-...-...
    >>> backup_timestamp0 == os.listdir('var/blobstoragebackups/')[0]
    True
    >>> backup_timestamp1 = os.listdir('var/blobstoragebackups/')[1]
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

    >>> write('var', 'blobstorage', 'blob3.txt', "Sample blob 3.")
    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt
    -  blob3.txt

Now try a restore.
The third file should be gone afterwards::

    >>> print system('bin/restore', input='no\n')
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/foo.fs
        /sample-buildout/var/filestorage/bar.fs
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage-foo
        /sample-buildout/var/blobstorage-bar
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Not restoring.
    <BLANKLINE>
    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt
    -  blob3.txt
    >>> print system('bin/restore', input='yes\n')
    --recover -o /sample-buildout/var/filestorage/foo.fs -r /sample-buildout/var/backups_foo
    --recover -o /sample-buildout/var/filestorage/bar.fs -r /sample-buildout/var/backups_bar
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/foo.fs
        /sample-buildout/var/filestorage/bar.fs
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage-foo
        /sample-buildout/var/blobstorage-bar
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-buildout/var/backups_foo to /sample-buildout/var/filestorage/foo.fs
    INFO: Please wait while restoring database file: /sample-buildout/var/backups_bar to /sample-buildout/var/filestorage/bar.fs
    INFO: Please wait while restoring database file: /sample-buildout/var/backups to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups_foo to /sample-buildout/var/blobstorage-foo
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups_foo/blobstorage-foo.20...-...-...-...-...-.../blobstorage-foo /sample-buildout/var
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups_bar to /sample-buildout/var/blobstorage-bar
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups_bar/blobstorage-bar.20...-...-...-...-...-.../blobstorage-bar /sample-buildout/var
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups/blobstorage.20...-...-...-...-...-.../blobstorage /sample-buildout/var
    <BLANKLINE>
    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt
    >>> cat('var', 'blobstorage', 'blob1.txt')
    Sample blob 1 version 3.

With the ``no-prompt`` option we avoid the question::

    >>> write('var', 'blobstorage', 'blob3.txt', "Sample blob 3.")
    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt
    -  blob3.txt
    >>> print system('bin/restore --no-prompt')
    --recover -o /sample-buildout/var/filestorage/foo.fs -r /sample-buildout/var/backups_foo
    --recover -o /sample-buildout/var/filestorage/bar.fs -r /sample-buildout/var/backups_bar
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups
    <BLANKLINE>
    INFO: Please wait while restoring database file: /sample-buildout/var/backups_foo to /sample-buildout/var/filestorage/foo.fs
    INFO: Please wait while restoring database file: /sample-buildout/var/backups_bar to /sample-buildout/var/filestorage/bar.fs
    INFO: Please wait while restoring database file: /sample-buildout/var/backups to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups_foo to /sample-buildout/var/blobstorage-foo
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups_foo/blobstorage-foo.20...-...-...-...-...-.../blobstorage-foo /sample-buildout/var
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups_bar to /sample-buildout/var/blobstorage-bar
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups_bar/blobstorage-bar.20...-...-...-...-...-.../blobstorage-bar /sample-buildout/var
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups/blobstorage.20...-...-...-...-...-.../blobstorage /sample-buildout/var
    <BLANKLINE>
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
    'blobstorage.20...-...-...-...-...-...'
    >>> time_string = backup_timestamp0[len('blobstorage.'):]
    >>> time_string
    '20...-...-...-...-...-...'
    >>> print system('bin/restore %s' % time_string, input='yes\n')
    --recover -o /sample-buildout/var/filestorage/foo.fs -r /sample-buildout/var/backups_foo -D ...
    --recover -o /sample-buildout/var/filestorage/bar.fs -r /sample-buildout/var/backups_bar -D ...
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups -D ...
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/foo.fs
        /sample-buildout/var/filestorage/bar.fs
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage-foo
        /sample-buildout/var/blobstorage-bar
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Date restriction: restoring state at ...
    INFO: Please wait while restoring database file: /sample-buildout/var/backups_foo to /sample-buildout/var/filestorage/foo.fs
    INFO: Please wait while restoring database file: /sample-buildout/var/backups_bar to /sample-buildout/var/filestorage/bar.fs
    INFO: Please wait while restoring database file: /sample-buildout/var/backups to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups_foo to /sample-buildout/var/blobstorage-foo
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups_foo/blobstorage-foo.20...-...-...-...-...-.../blobstorage-foo /sample-buildout/var
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups_bar to /sample-buildout/var/blobstorage-bar
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups_bar/blobstorage-bar.20...-...-...-...-...-.../blobstorage-bar /sample-buildout/var
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups/blobstorage.20...-...-...-...-...-.../blobstorage /sample-buildout/var
    <BLANKLINE>

The second blob file is now no longer in the blob storage.

    >>> ls('var/blobstorage')
    -  blob1.txt

The first blob file is back to an earlier version::

    >>> cat('var', 'blobstorage', 'blob1.txt')
    Sample blob 1 version 2.

The snapshotrestore works too::

    >>> print system('bin/snapshotrestore', input='yes\n')
    --recover -o /sample-buildout/var/filestorage/foo.fs -r /sample-buildout/var/snapshotbackups_foo
    --recover -o /sample-buildout/var/filestorage/bar.fs -r /sample-buildout/var/snapshotbackups_bar
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/snapshotbackups
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/foo.fs
        /sample-buildout/var/filestorage/bar.fs
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage-foo
        /sample-buildout/var/blobstorage-bar
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-buildout/var/snapshotbackups_foo to /sample-buildout/var/filestorage/foo.fs
    INFO: Please wait while restoring database file: /sample-buildout/var/snapshotbackups_bar to /sample-buildout/var/filestorage/bar.fs
    INFO: Please wait while restoring database file: /sample-buildout/var/snapshotbackups to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/blobstoragesnapshots_foo to /sample-buildout/var/blobstorage-foo
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragesnapshots_foo/blobstorage-foo.20...-...-...-...-...-.../blobstorage-foo /sample-buildout/var
    INFO: Restoring blobs from /sample-buildout/var/blobstoragesnapshots_bar to /sample-buildout/var/blobstorage-bar
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragesnapshots_bar/blobstorage-bar.20...-...-...-...-...-.../blobstorage-bar /sample-buildout/var
    INFO: Restoring blobs from /sample-buildout/var/blobstoragesnapshots to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragesnapshots/blobstorage.20...-...-...-...-...-.../blobstorage /sample-buildout/var
    <BLANKLINE>

Check that this fits what is in the most recent snapshot::

    >>> ls('var/blobstorage')
    -  blob1.txt
    >>> ls('var/blobstoragesnapshots')
    d  blobstorage.20...-...-...-...-...-...
    d  blobstorage.20...-...-...-...-...-...
    d  blobstorage.20...-...-...-...-...-...
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
    'blobstorage.20...-...-...-...-...-...'
    >>> time_string = timestamp1[len('blobstorage.'):]
    >>> time_string
    '20...-...-...-...-...-...'
    >>> print system('bin/snapshotrestore %s' % time_string, input='yes\n')
    --recover -o /sample-buildout/var/filestorage/foo.fs -r /sample-buildout/var/snapshotbackups_foo -D ...
    --recover -o /sample-buildout/var/filestorage/bar.fs -r /sample-buildout/var/snapshotbackups_bar -D ...
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/snapshotbackups -D ...
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/foo.fs
        /sample-buildout/var/filestorage/bar.fs
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage-foo
        /sample-buildout/var/blobstorage-bar
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Date restriction: restoring state at ...
    INFO: Please wait while restoring database file: /sample-buildout/var/snapshotbackups_foo to /sample-buildout/var/filestorage/foo.fs
    INFO: Please wait while restoring database file: /sample-buildout/var/snapshotbackups_bar to /sample-buildout/var/filestorage/bar.fs
    INFO: Please wait while restoring database file: /sample-buildout/var/snapshotbackups to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/blobstoragesnapshots_foo to /sample-buildout/var/blobstorage-foo
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragesnapshots_foo/blobstorage-foo.20...-...-...-...-...-.../blobstorage-foo /sample-buildout/var
    INFO: Restoring blobs from /sample-buildout/var/blobstoragesnapshots_bar to /sample-buildout/var/blobstorage-bar
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragesnapshots_bar/blobstorage-bar.20...-...-...-...-...-.../blobstorage-bar /sample-buildout/var
    INFO: Restoring blobs from /sample-buildout/var/blobstoragesnapshots to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragesnapshots/blobstorage.20...-...-...-...-...-.../blobstorage /sample-buildout/var
    <BLANKLINE>

The second blob file was only in blobstorage snapshot number 1 when we
started and now it is also in the main blobstorage again.

    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt
    >>> cat('var', 'blobstorage', 'blob1.txt')
    Sample blob 1.


zipbackup and ziprestore and timestamps
---------------------------------------

This is adapted from zipbackup.rst.

Since version 2.20, we can create a zipbackup and ziprestore
script.  These use a different backup location and have a few options
hardcoded: gzip and archive_blob are True, keep is 1, regardless of what
the options in the buildout recipe section are.  You can always create
a separate buildout section where you explicitly change this using
options for the standard bin/backup script.

By default the scripts are not created.  You can enable them by
setting the enable_zipbackup option to true.

Create some archived (gzipped) and not-archived separate backup scripts::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... blob_timestamps = true
    ... enable_zipbackup = true
    ... """)
    >>> print system(buildout)
    Uninstalling backup.
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/zipbackup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/ziprestore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    <BLANKLINE>

Now we test it::

    >>> print system('bin/zipbackup')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/zipbackups -F --gzip
    INFO: Created /sample-buildout/var/zipbackups
    INFO: Created /sample-buildout/var/blobstoragezips
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/zipbackups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragezips
    INFO: tar cf /sample-buildout/var/blobstoragezips/blobstorage.20...-...-...-...-...-....tar -C /sample-buildout/var/blobstorage .
    <BLANKLINE>
    >>> ls('var', 'blobstoragezips')
    -   blobstorage.20...-...-...-...-...-....tar
    >>> zip_timestamp0 = os.listdir('var/blobstoragezips')[0]

Keep is ignored by zipbackup, always using 1 as value.
Pause a short time to avoid getting an error for overwriting the previous file::

    >>> time.sleep(1)
    >>> print system('bin/zipbackup')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/zipbackups -F --gzip
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/zipbackups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragezips
    INFO: tar cf /sample-buildout/var/blobstoragezips/blobstorage.20...-...-...-...-...-....tar -C /sample-buildout/var/blobstorage .
    INFO: Removed 1 blob backup(s), the latest 1 backup(s) have been kept.
    <BLANKLINE>
    >>> ls('var', 'blobstoragezips')
    -   blobstorage.20...-...-...-...-...-....tar
    >>> zip_timestamp1 = os.listdir('var/blobstoragezips')[0]
    >>> zip_timestamp0 == zip_timestamp1
    False

Now test the ziprestore script::

    >>> print system('bin/ziprestore', input='yes\n')
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/zipbackups
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-buildout/var/zipbackups to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/blobstoragezips to /sample-buildout/var/blobstorage
    INFO: Removing /sample-buildout/var/blobstorage
    INFO: Extracting /sample-buildout/var/blobstoragezips/blobstorage.20...-...-...-...-...-....tar to /sample-buildout/var/blobstorage
    INFO: tar xf /sample-buildout/var/blobstoragezips/blobstorage.20...-...-...-...-...-....tar -C /sample-buildout/var/blobstorage
    <BLANKLINE>
