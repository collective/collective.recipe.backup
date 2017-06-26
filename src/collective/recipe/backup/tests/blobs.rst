# -*-doctest-*-

Blob storage
============

For tests with ``blob_timestamps = true``, see ``blob_timestamps.rst``.
That started as a copy of the current ``blobs.rst`` file.

Just to isolate some test differences, we run an empty buildout once::

    >>> ignore = system(buildout)

Add mock ``bin/repozo`` script::

    >>> import sys
    >>> write('bin', 'repozo',
    ...       "#!%s\nimport sys\nprint ' '.join(sys.argv[1:])" % sys.executable)
    >>> dontcare = system('chmod u+x bin/repozo')

New in this recipe is that we backup the blob storage.  Plone 4 uses a
blob storage to store files on the file system.  In Plone 3 this is
optional.  When this is used, it should be backed up of course.  You
must specify the source blob_storage directory where Plone (or Zope)
stores its blobs.  When we do not set it specifically, we try to get
the location from the plone.recipe.zope2instance recipe (or a
zeoserver recipe) when it is used::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... # For some reason this is now needed:
    ... index = http://pypi.python.org/simple
    ... # Avoid suddenly updating zc.buildout or other packages:
    ... newest = false
    ... parts = instance backup
    ... versions = versions
    ...
    ... [versions]
    ... # A slightly older version that does not rely on the Zope2 egg
    ... plone.recipe.zope2instance = 3.9
    ... mailinglogger = 3.3
    ...
    ... [instance]
    ... # The recipe should be all lower case, but it actually works
    ... # when you accidentally have uppercase, so we should accept
    ... # this too.
    ... recipe = plone.recipe.zope2INSTANCE
    ... user = admin:admin
    ... blob-storage = ${buildout:directory}/var/somewhere
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... """)

We need a mock mkzopeinstance script in the bin directory for the
zope2instance recipe to work:

    >>> write('bin/mkzopeinstance', """
    ... import sys
    ... import os
    ... path = sys.argv[2]
    ... os.mkdir(path)
    ... os.mkdir(os.path.join(path, 'etc'))
    ... """)

We run the buildout (and set a timeout as we need a few new packages
and apparently a few servers are currently down so a timeout helps
speed things up a bit):

    >>> print system('bin/buildout -t 5')
    Setting socket time out to 5 seconds.
    Getting distribution for 'plone.recipe.zope2INSTANCE==3.9'...
    Got plone.recipe.zope2instance 3.9.
    Getting distribution for 'mailinglogger==3.3'...
    Got mailinglogger 3.3.0.
    Installing instance.
    Generated script '/sample-buildout/bin/instance'.
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'...
    <BLANKLINE>
    >>> ls('bin')
    -  backup
    -  buildout
    -  instance
    -  mkzopeinstance
    -  repozo
    -  restore
    -  snapshotbackup
    -  snapshotrestore
    >>> cat('bin/backup')
    #!...
    ...blob_backup_location.../var/blobstoragebackups...
    ...blob_snapshot_location.../var/blobstoragesnapshots...
    ...blob_zip_location.../var/blobstoragezips...
    ...blobdir.../var/somewhere...
    ...datafs.../var/filestorage/Data.fs...
    ...snapshot_location.../var/snapshotbackups...
    ...storage...1...
    ...zip_location.../var/zipbackups...

Without explicit blob-storage option, it defaults to ``blobstorage`` in the var directory, which might be somewhere else.

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... index = http://pypi.python.org/simple
    ... # Avoid suddenly updating zc.buildout or other packages:
    ... newest = false
    ... parts = instance backup
    ... versions = versions
    ...
    ... [versions]
    ... # A slightly older version that does not rely on the Zope2 egg
    ... plone.recipe.zope2instance = 3.9
    ... mailinglogger = 3.3
    ...
    ... [instance]
    ... recipe = plone.recipe.zope2instance
    ... user = admin:admin
    ... var = ${buildout:directory}/var/another/
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... """)
    >>> print system('bin/buildout')
    Uninstalling instance.
    Installing instance.
    Updating backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'...
    <BLANKLINE>
    >>> ls('bin')
    -  backup
    -  buildout
    -  instance
    -  mkzopeinstance
    -  repozo
    -  restore
    -  snapshotbackup
    -  snapshotrestore
    >>> cat('bin/backup')
    #!...
    ...blob_backup_location.../var/another/blobstoragebackups...
    ...blob_snapshot_location.../var/another/blobstoragesnapshots...
    ...blob_zip_location.../var/another/blobstoragezips...
    ...blobdir.../var/another/blobstorage...
    ...datafs.../var/another/filestorage/Data.fs...
    ...snapshot_location.../var/another/snapshotbackups...
    ...storage...1...
    ...zip_location.../var/another/zipbackups...

Nowadays it is strange to not have a blob storage, at least with Plone
4 and higher.  So we bail out when this is the case.

We will only do this when we are being run with Python 2.6 or higher,
because Python 2.4 indicates we are still on Plone 3.  Note that
Python 2.4 / Plone 3 is not officially supported, and is not tested.
Main reason is that is was too difficult to keep the tests passing in
Plone 3 and Plone 4.  But the recipe should still work, so let's at
least not break it on purpose or make it harder.  So the following
is only for Plone 4 and higher.

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... """)
    >>> print system(buildout)
    Uninstalling instance.
    Updating backup.
    While:
      Updating backup.
    Error: No blob_storage found. You must specify one. To ignore this, set 'backup_blobs = false' in the [backup] section.
    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... """)
    >>> print system(buildout)
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    <BLANKLINE>

We can override the additional_filestorages location:

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
    ...    catalog ${buildout:directory}/var/filestorage/2.fs
    ... """)
    >>> print system(buildout)
    Uninstalling backup.
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    <BLANKLINE>


We can override the additional_filestorages blob source location:

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = True
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... additional_filestorages =
    ...    withblob    ${buildout:directory}/var/filestorage/2.fs ${buildout:directory}/var/blobstorage2
    ...    withoutblob ${buildout:directory}/var/filestorage/3.fs
    ... """)
    >>> print system(buildout)
    Uninstalling backup.
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    <BLANKLINE>

Wrong configurations for additional_filestorages:

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
    ...    wrong ${buildout:directory}/var/filestorage foo.fs ${buildout:directory}/var/blobstorage_foo
    ... """)
    >>> print system(buildout)
    Uninstalling backup.
    Installing backup.
    While:
       Installing backup.
    ...
    AttributeError: 'NoneType' object has no attribute 'groupdict'
    <BLANKLINE>

Full cycle tests:

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... keep = 3
    ... additional_filestorages =
    ...    foo ${buildout:directory}/var/filestorage/foo.fs ${buildout:directory}/var/blobstorage-foo
    ...    bar ${buildout:directory}/var/filestorage/bar.fs ${buildout:directory}/var/blobstorage-bar/
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
    -  instance
    -  mkzopeinstance
    -  repozo
    -  restore
    -  snapshotbackup
    -  snapshotrestore
    >>> mkdir('var/blobstorage')
    >>> write('var', 'blobstorage', 'blob1.txt', "Sample blob 1.")
    >>> mkdir('var/blobstorage-foo')
    >>> write('var', 'blobstorage-foo', 'blob-foo1.txt', "Sample blob foo 1.")
    >>> mkdir('var/blobstorage-bar')
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
    INFO: rsync -a  /sample-buildout/var/blobstorage-foo /sample-buildout/var/blobstoragesnapshots_foo/blobstorage-foo.0
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage-bar to /sample-buildout/var/blobstoragesnapshots_bar
    INFO: rsync -a  /sample-buildout/var/blobstorage-bar /sample-buildout/var/blobstoragesnapshots_bar/blobstorage-bar.0
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots
    INFO: rsync -a  /sample-buildout/var/blobstorage /sample-buildout/var/blobstoragesnapshots/blobstorage.0
    <BLANKLINE>
    >>> ls('var/blobstoragesnapshots')
    d  blobstorage.0
    >>> ls('var/blobstoragesnapshots/blobstorage.0')
    d  blobstorage
    >>> ls('var/blobstoragesnapshots_foo')
    d  blobstorage-foo.0
    >>> ls('var/blobstoragesnapshots_foo/blobstorage-foo.0')
    d  blobstorage-foo
    >>> ls('var/blobstoragesnapshots_bar')
    d  blobstorage-bar.0
    >>> ls('var/blobstoragesnapshots_bar/blobstorage-bar.0')
    d  blobstorage-bar

Let's try that some more, with a second in between so we can more
easily test restoring to a specific time later.

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
    INFO: Renaming blobstorage-foo.0 to blobstorage-foo.1.
    INFO: rsync -a  --delete --link-dest=../blobstorage-foo.1 /sample-buildout/var/blobstorage-foo /sample-buildout/var/blobstoragesnapshots_foo/blobstorage-foo.0
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage-bar to /sample-buildout/var/blobstoragesnapshots_bar
    INFO: Renaming blobstorage-bar.0 to blobstorage-bar.1.
    INFO: rsync -a  --delete --link-dest=../blobstorage-bar.1 /sample-buildout/var/blobstorage-bar /sample-buildout/var/blobstoragesnapshots_bar/blobstorage-bar.0
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots
    INFO: Renaming blobstorage.0 to blobstorage.1.
    INFO: rsync -a  --delete --link-dest=../blobstorage.1 /sample-buildout/var/blobstorage /sample-buildout/var/blobstoragesnapshots/blobstorage.0
    <BLANKLINE>
    >>> ls('var/blobstoragesnapshots')
    d  blobstorage.0
    d  blobstorage.1
    >>> ls('var/blobstoragesnapshots/blobstorage.0/blobstorage')
    -  blob1.txt
    -  blob2.txt
    >>> ls('var/blobstoragesnapshots/blobstorage.1/blobstorage')
    -  blob1.txt
    >>> cat('var/blobstoragesnapshots/blobstorage.0/blobstorage/blob1.txt')
    Sample blob 1.
    >>> cat('var/blobstoragesnapshots/blobstorage.0/blobstorage/blob2.txt')
    Sample blob 2.
    >>> cat('var/blobstoragesnapshots/blobstorage.1/blobstorage/blob1.txt')
    Sample blob 1.
    >>> ls('var/blobstoragesnapshots_foo')
    d  blobstorage-foo.0
    d  blobstorage-foo.1
    >>> ls('var/blobstoragesnapshots_foo/blobstorage-foo.0/blobstorage-foo')
    -  blob-foo1.txt
    -  blob-foo2.txt
    >>> ls('var/blobstoragesnapshots_foo/blobstorage-foo.1/blobstorage-foo')
    -  blob-foo1.txt
    >>> cat('var/blobstoragesnapshots_foo/blobstorage-foo.0/blobstorage-foo/blob-foo1.txt')
    Sample blob foo 1.
    >>> cat('var/blobstoragesnapshots_foo/blobstorage-foo.0/blobstorage-foo/blob-foo2.txt')
    Sample blob foo 2.
    >>> cat('var/blobstoragesnapshots_foo/blobstorage-foo.1/blobstorage-foo/blob-foo1.txt')
    Sample blob foo 1.

Now remove an item:

    >>> time.sleep(2)
    >>> remove('var', 'blobstorage', 'blob2.txt')
    >>> remove('var', 'blobstorage-foo', 'blob-foo1.txt')
    >>> remove('var', 'blobstorage-bar', 'blob-bar1.txt')
    >>> print system('bin/snapshotbackup')
    --backup -f /sample-buildout/var/filestorage/foo.fs -r /sample-buildout/var/snapshotbackups_foo -F --gzip
    --backup -f /sample-buildout/var/filestorage/bar.fs -r /sample-buildout/var/snapshotbackups_bar -F --gzip
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/snapshotbackups -F --gzip
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/foo.fs to /sample-buildout/var/snapshotbackups_foo
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/bar.fs to /sample-buildout/var/snapshotbackups_bar
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/snapshotbackups
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage-foo to /sample-buildout/var/blobstoragesnapshots_foo
    INFO: Renaming blobstorage-foo.1 to blobstorage-foo.2.
    INFO: Renaming blobstorage-foo.0 to blobstorage-foo.1.
    INFO: rsync -a  --delete --link-dest=../blobstorage-foo.1 /sample-buildout/var/blobstorage-foo /sample-buildout/var/blobstoragesnapshots_foo/blobstorage-foo.0
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage-bar to /sample-buildout/var/blobstoragesnapshots_bar
    INFO: Renaming blobstorage-bar.1 to blobstorage-bar.2.
    INFO: Renaming blobstorage-bar.0 to blobstorage-bar.1.
    INFO: rsync -a  --delete --link-dest=../blobstorage-bar.1 /sample-buildout/var/blobstorage-bar /sample-buildout/var/blobstoragesnapshots_bar/blobstorage-bar.0
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragesnapshots
    INFO: Renaming blobstorage.1 to blobstorage.2.
    INFO: Renaming blobstorage.0 to blobstorage.1.
    INFO: rsync -a  --delete --link-dest=../blobstorage.1 /sample-buildout/var/blobstorage /sample-buildout/var/blobstoragesnapshots/blobstorage.0
    <BLANKLINE>
    >>> ls('var/blobstoragesnapshots')
    d  blobstorage.0
    d  blobstorage.1
    d  blobstorage.2
    >>> ls('var/blobstoragesnapshots/blobstorage.0/blobstorage')
    -  blob1.txt
    >>> ls('var/blobstoragesnapshots/blobstorage.1/blobstorage')
    -  blob1.txt
    -  blob2.txt
    >>> ls('var/blobstoragesnapshots/blobstorage.2/blobstorage')
    -  blob1.txt
    >>> ls('var/blobstoragesnapshots_foo')
    d  blobstorage-foo.0
    d  blobstorage-foo.1
    d  blobstorage-foo.2
    >>> ls('var/blobstoragesnapshots_foo/blobstorage-foo.0/blobstorage-foo')
    -  blob-foo2.txt
    >>> ls('var/blobstoragesnapshots_foo/blobstorage-foo.1/blobstorage-foo')
    -  blob-foo1.txt
    -  blob-foo2.txt
    >>> ls('var/blobstoragesnapshots_foo/blobstorage-foo.2/blobstorage-foo')
    -  blob-foo1.txt

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
    INFO: rsync -a  /sample-buildout/var/blobstorage-foo /sample-buildout/var/blobstoragebackups_foo/blobstorage-foo.0
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage-bar to /sample-buildout/var/blobstoragebackups_bar
    INFO: rsync -a  /sample-buildout/var/blobstorage-bar /sample-buildout/var/blobstoragebackups_bar/blobstorage-bar.0
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups
    INFO: rsync -a  /sample-buildout/var/blobstorage /sample-buildout/var/blobstoragebackups/blobstorage.0
    <BLANKLINE>
    >>> ls('var/blobstoragebackups')
    d  blobstorage.0
    >>> ls('var/blobstoragebackups/blobstorage.0')
    d  blobstorage
    >>> ls('var/blobstoragebackups/blobstorage.0/blobstorage')
    -  blob1.txt
    >>> ls('var/blobstoragebackups_foo')
    d  blobstorage-foo.0
    >>> ls('var/blobstoragebackups_foo/blobstorage-foo.0')
    d  blobstorage-foo
    >>> ls('var/blobstoragebackups_foo/blobstorage-foo.0/blobstorage-foo')
    -  blob-foo2.txt

We try again with an extra 'blob':

    >>> time.sleep(2)
    >>> write('var', 'blobstorage', 'blob2.txt', "Sample blob 2.")
    >>> print system('bin/backup')
    --backup -f /sample-buildout/var/filestorage/foo.fs -r /sample-buildout/var/backups_foo --quick --gzip
    --backup -f /sample-buildout/var/filestorage/bar.fs -r /sample-buildout/var/backups_bar --quick --gzip
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups --quick --gzip
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/foo.fs to /sample-buildout/var/backups_foo
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/bar.fs to /sample-buildout/var/backups_bar
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/backups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage-foo to /sample-buildout/var/blobstoragebackups_foo
    INFO: Renaming blobstorage-foo.0 to blobstorage-foo.1.
    INFO: rsync -a  --delete --link-dest=../blobstorage-foo.1 /sample-buildout/var/blobstorage-foo /sample-buildout/var/blobstoragebackups_foo/blobstorage-foo.0
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage-bar to /sample-buildout/var/blobstoragebackups_bar
    INFO: Renaming blobstorage-bar.0 to blobstorage-bar.1.
    INFO: rsync -a  --delete --link-dest=../blobstorage-bar.1 /sample-buildout/var/blobstorage-bar /sample-buildout/var/blobstoragebackups_bar/blobstorage-bar.0
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups
    INFO: Renaming blobstorage.0 to blobstorage.1.
    INFO: rsync -a  --delete --link-dest=../blobstorage.1 /sample-buildout/var/blobstorage /sample-buildout/var/blobstoragebackups/blobstorage.0
    <BLANKLINE>
    >>> ls('var/blobstoragebackups')
    d  blobstorage.0
    d  blobstorage.1
    >>> ls('var/blobstoragebackups/blobstorage.0/blobstorage')
    -  blob1.txt
    -  blob2.txt
    >>> ls('var/blobstoragebackups/blobstorage.1/blobstorage')
    -  blob1.txt

Let's check the inodes of two files, to see if they are the same.  Not
sure if this works on all operating systems.

    >>> import os
    >>> stat_0 = os.stat('var/blobstoragebackups/blobstorage.0/blobstorage/blob1.txt')
    >>> stat_1 = os.stat('var/blobstoragebackups/blobstorage.1/blobstorage/blob1.txt')
    >>> stat_0.st_ino == stat_1.st_ino
    True

We could to things differently for the snapshot blob backups, as they
should be full copies, but using hard links they also really are full
copies, so also in this case the inodes can be the same::

    >>> stat_0 = os.stat('var/blobstoragesnapshots/blobstorage.0/blobstorage/blob1.txt')
    >>> stat_1 = os.stat('var/blobstoragesnapshots/blobstorage.1/blobstorage/blob1.txt')
    >>> stat_0.st_ino == stat_1.st_ino
    True

Now try a restore::

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
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups_foo/blobstorage-foo.0/blobstorage-foo /sample-buildout/var
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups_bar to /sample-buildout/var/blobstorage-bar
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups_bar/blobstorage-bar.0/blobstorage-bar /sample-buildout/var
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups/blobstorage.0/blobstorage /sample-buildout/var
    <BLANKLINE>
    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt

With the ``no-prompt`` option we avoid the question::

    >>> print system('bin/restore --no-prompt')
    --recover -o /sample-buildout/var/filestorage/foo.fs -r /sample-buildout/var/backups_foo
    --recover -o /sample-buildout/var/filestorage/bar.fs -r /sample-buildout/var/backups_bar
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups
    <BLANKLINE>
    INFO: Please wait while restoring database file: /sample-buildout/var/backups_foo to /sample-buildout/var/filestorage/foo.fs
    INFO: Please wait while restoring database file: /sample-buildout/var/backups_bar to /sample-buildout/var/filestorage/bar.fs
    INFO: Please wait while restoring database file: /sample-buildout/var/backups to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups_foo to /sample-buildout/var/blobstorage-foo
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups_foo/blobstorage-foo.0/blobstorage-foo /sample-buildout/var
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups_bar to /sample-buildout/var/blobstorage-bar
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups_bar/blobstorage-bar.0/blobstorage-bar /sample-buildout/var
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups/blobstorage.0/blobstorage /sample-buildout/var
    <BLANKLINE>
    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt

Since release 2.3 we can also restore blobs to a specific date/time.
blobstorage.0 is the newest, blobstorage.1 is the oldest.  The restore
script will restore the first blobstorage with a modification time the
same or earlier than the time we ask for.  Here we ask for a time that
should be the same as the modification date of blobstorage.1.  We
add a second to avoid random errors that have plagued these
tests due to rounding or similar sillyness.

    >>> mod_time_0 = os.path.getmtime('var/blobstoragebackups/blobstorage.0')
    >>> mod_time_1 = os.path.getmtime('var/blobstoragebackups/blobstorage.1')
    >>> mod_time_0 > mod_time_1
    True
    >>> from datetime import datetime
    >>> time_string = '-'.join(['{0:02d}'.format(t) for t in datetime.utcfromtimestamp(mod_time_1 + 1).timetuple()[:6]])
    >>> mod_time_0 = os.path.getmtime('var/blobstoragebackups_bar/blobstorage-bar.0')
    >>> mod_time_1 = os.path.getmtime('var/blobstoragebackups_bar/blobstorage-bar.1')
    >>> mod_time_0 > mod_time_1
    True
    >>> mod_time_0 = os.path.getmtime('var/blobstoragebackups_foo/blobstorage-foo.0')
    >>> mod_time_1 = os.path.getmtime('var/blobstoragebackups_foo/blobstorage-foo.1')
    >>> mod_time_0 > mod_time_1
    True
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
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups_foo/blobstorage-foo.1/blobstorage-foo /sample-buildout/var
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups_bar to /sample-buildout/var/blobstorage-bar
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups_bar/blobstorage-bar.1/blobstorage-bar /sample-buildout/var
    INFO: Restoring blobs from /sample-buildout/var/blobstoragebackups to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragebackups/blobstorage.1/blobstorage /sample-buildout/var
    <BLANKLINE>

The second blob file is now no longer in the blob storage.

    >>> ls('var/blobstorage')
    -  blob1.txt

When passed a date for which we have no backups, the script will fail.

    >>> print system('bin/restore 1972-12-25', input='yes\n')
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
    INFO: Date restriction: restoring state at 1972-12-25.
    ERROR: Could not find backup of '1972-12-25' or earlier.
    ERROR: Halting execution: restoring blobstorages would fail.
    <BLANKLINE>

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
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragesnapshots_foo/blobstorage-foo.0/blobstorage-foo /sample-buildout/var
    INFO: Restoring blobs from /sample-buildout/var/blobstoragesnapshots_bar to /sample-buildout/var/blobstorage-bar
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragesnapshots_bar/blobstorage-bar.0/blobstorage-bar /sample-buildout/var
    INFO: Restoring blobs from /sample-buildout/var/blobstoragesnapshots to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragesnapshots/blobstorage.0/blobstorage /sample-buildout/var
    <BLANKLINE>

Check that this fits what is in the most recent snapshot::

    >>> ls('var/blobstorage')
    -  blob1.txt
    >>> ls('var/blobstoragesnapshots')
    d  blobstorage.0
    d  blobstorage.1
    d  blobstorage.2
    >>> ls('var/blobstoragesnapshots/blobstorage.0/blobstorage')
    -  blob1.txt
    >>> ls('var/blobstoragesnapshots/blobstorage.1/blobstorage')
    -  blob1.txt
    -  blob2.txt
    >>> ls('var/blobstoragesnapshots/blobstorage.2/blobstorage')
    -  blob1.txt

Since release 2.3 we can also restore blob snapshots to a specific date/time.

    >>> mod_time_0 = os.path.getmtime('var/blobstoragesnapshots/blobstorage.0')
    >>> mod_time_1 = os.path.getmtime('var/blobstoragesnapshots/blobstorage.1')
    >>> mod_time_2 = os.path.getmtime('var/blobstoragesnapshots/blobstorage.2')
    >>> mod_time_0 > mod_time_1
    True
    >>> mod_time_1 > mod_time_2
    True
    >>> time_string = '-'.join(['{0:02d}'.format(t) for t in datetime.utcfromtimestamp(mod_time_1 + 1).timetuple()[:6]])
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
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragesnapshots_foo/blobstorage-foo.1/blobstorage-foo /sample-buildout/var
    INFO: Restoring blobs from /sample-buildout/var/blobstoragesnapshots_bar to /sample-buildout/var/blobstorage-bar
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragesnapshots_bar/blobstorage-bar.1/blobstorage-bar /sample-buildout/var
    INFO: Restoring blobs from /sample-buildout/var/blobstoragesnapshots to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/var/blobstoragesnapshots/blobstorage.1/blobstorage /sample-buildout/var
    <BLANKLINE>

The second blob file was only in blobstorage snapshot number 1 when we
started and now it is also in the main blobstorage again.

    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt

When repozo quits with an error, we should not restore the blobs then either.
We test that with a special bin/repozo script that simply quits::

    >>> write('bin', 'repozo', "#!%s\nimport sys\nsys.exit(1)" % sys.executable)
    >>> dontcare = system('chmod u+x bin/repozo')
    >>> print system('bin/snapshotrestore', input='yes\n')
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
    ERROR: Repozo command failed. See message above.
    ERROR: Halting execution due to error; not restoring blobs.
    <BLANKLINE>

Restore the original bin/repozo::

    >>> write('bin', 'repozo',
    ...       "#!%s\nimport sys\nprint ' '.join(sys.argv[1:])" % sys.executable)
    >>> dontcare = system('chmod u+x bin/repozo')


We can tell buildout that we only want to backup blobs or specifically
do not want to backup the blobs.

When we explicitly set backup_blobs to true, we must have a
blob_storage option, otherwise buildout quits::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = true
    ... """)
    >>> print system(buildout)
    Uninstalling backup.
    Installing backup.
    While:
      Installing backup.
    Error: No blob_storage found. You must specify one. To ignore this, set 'backup_blobs = false' in the [backup] section.
    <BLANKLINE>

Combining blob_backup=false and only_blobs=true will not work::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... backup_blobs = false
    ... only_blobs = true
    ... """)
    >>> print system(buildout)
    While:
      Installing.
      Getting section backup.
      Initializing section backup.
    Error: Cannot have backup_blobs false and only_blobs true.
    <BLANKLINE>

Specifying backup_blobs and only_blobs might be useful in case you
want to separate this into several scripts.  Let's specify
enable_zipbackup too::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = filebackup blobbackup
    ...
    ... [filebackup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... backup_blobs = false
    ...
    ... [blobbackup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... only_blobs = true
    ... enable_zipbackup = true
    ... """)
    >>> print system(buildout)
    Installing filebackup.
    Generated script '/sample-buildout/bin/filebackup'.
    Generated script '/sample-buildout/bin/filebackup-snapshot'.
    Generated script '/sample-buildout/bin/filebackup-restore'.
    Generated script '/sample-buildout/bin/filebackup-snapshotrestore'.
    Installing blobbackup.
    Generated script '/sample-buildout/bin/blobbackup'.
    Generated script '/sample-buildout/bin/blobbackup-zip'.
    Generated script '/sample-buildout/bin/blobbackup-snapshot'.
    Generated script '/sample-buildout/bin/blobbackup-restore'.
    Generated script '/sample-buildout/bin/blobbackup-ziprestore'.
    Generated script '/sample-buildout/bin/blobbackup-snapshotrestore'.
    <BLANKLINE>

Now we test it.  First the backup.  The filebackup now only backs up
the filestorage::

    >>> print system('bin/filebackup')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/filebackups --quick --gzip
    INFO: Created /sample-buildout/var/filebackups
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/filebackups
    <BLANKLINE>

blobbackup only backs up the blobstorage::

    >>> print system('bin/blobbackup')
    INFO: Created /sample-buildout/var/blobbackup-blobstorages
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobbackup-blobstorages
    INFO: rsync -a  /sample-buildout/var/blobstorage /sample-buildout/var/blobbackup-blobstorages/blobstorage.0
    <BLANKLINE>

Test the snapshots as well::

    >>> print system('bin/filebackup-snapshot')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/filebackup-snapshots -F --gzip
    INFO: Created /sample-buildout/var/filebackup-snapshots
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/filebackup-snapshots
    <BLANKLINE>
    >>> print system('bin/blobbackup-snapshot')
    INFO: Created /sample-buildout/var/blobbackup-blobstoragesnapshots
    INFO: Please wait while making snapshot of blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobbackup-blobstoragesnapshots
    INFO: rsync -a  /sample-buildout/var/blobstorage /sample-buildout/var/blobbackup-blobstoragesnapshots/blobstorage.0
    <BLANKLINE>

Now test the restore::

    >>> print system('bin/filebackup-restore', input='yes\n')
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/filebackups
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-buildout/var/filebackups to /sample-buildout/var/filestorage/Data.fs
    <BLANKLINE>
    >>> print system('bin/filebackup-snapshotrestore', input='yes\n')
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/filebackup-snapshots
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-buildout/var/filebackup-snapshots to /sample-buildout/var/filestorage/Data.fs
    <BLANKLINE>
    >>> print system('bin/blobbackup-restore', input='yes\n')
    <BLANKLINE>
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Restoring blobs from /sample-buildout/var/blobbackup-blobstorages to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/var/blobbackup-blobstorages/blobstorage.0/blobstorage /sample-buildout/var
    <BLANKLINE>
    >>> print system('bin/blobbackup-snapshotrestore', input='yes\n')
    <BLANKLINE>
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Restoring blobs from /sample-buildout/var/blobbackup-blobstoragesnapshots to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/var/blobbackup-blobstoragesnapshots/blobstorage.0/blobstorage /sample-buildout/var
    <BLANKLINE>

Test extra rsync options, currently only testing --no-l -k to allow
for symlinked directory dereferencing in restore. We use this to test
passing of valid rsync options additional to the default -a
option. Since all backup and restore variants with blobs and using
rsync use the same code, we only need to test the standard backup and
restore to ensure passing of extra options to rsync works::

    >>> # first remove some previously created directories interfering with this test
    >>> import shutil
    >>> shutil.rmtree('var/blobstoragebackups/blobstorage.0')
    >>> shutil.rmtree('var/blobstoragebackups/blobstorage.1')
    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... rsync_options = --no-l -k
    ... """)
    >>> print system(buildout)
    Uninstalling blobbackup.
    Uninstalling filebackup.
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    <BLANKLINE>
    >>> ls('bin')
    - backup
    - buildout
    - instance
    - mkzopeinstance
    - repozo
    - restore
    - snapshotbackup
    - snapshotrestore
    >>> print system('bin/backup')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups --quick --gzip
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/backups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups
    INFO: rsync -a --no-l -k /sample-buildout/var/blobstorage /sample-buildout/var/blobstoragebackups/blobstorage.0
    <BLANKLINE>
    >>> ls('var/blobstoragebackups')
    d  blobstorage.0
    >>> ls('var/blobstoragebackups/blobstorage.0')
    d  blobstorage
    >>> ls('var/blobstoragebackups/blobstorage.0/blobstorage')
    -  blob1.txt
    -  blob2.txt

So backup still works, now test restore that uses a symlinked directory as the backup source::

    >>> # first remove blobs from blobstorage as we are testing restore
    >>> remove('var','blobstorage','blob1.txt')
    >>> remove('var','blobstorage','blob2.txt')
    >>> mkdir('var/test')
    >>> mkdir('var/test/blobstorage.0')
    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... blobbackuplocation = ${buildout:directory}/var/test
    ... rsync_options = --no-l -k
    ... # we use pre_ and post_commands to set/unset the symlink
    ... # using os.symlink instead causes rsync to fail for some reason
    ... pre_command = ln -s ${buildout:directory}/var/blobstoragebackups/blobstorage.0/blobstorage ${backup:blobbackuplocation}/blobstorage.0/blobstorage
    ... post_command = unlink ${backup:blobbackuplocation}/blobstorage.0/blobstorage
    ... """)
    >>> print system(buildout)
    Uninstalling backup.
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    <BLANKLINE>
    >>> ls('bin')
    - backup
    - buildout
    - instance
    - mkzopeinstance
    - repozo
    - restore
    - snapshotbackup
    - snapshotrestore
    >>> print system('bin/restore --no-prompt')
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups
    <BLANKLINE>
    INFO: Please wait while restoring database file: /sample-buildout/var/backups to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/test to /sample-buildout/var/blobstorage
    INFO: rsync -a --no-l -k --delete /sample-buildout/var/test/blobstorage.0/blobstorage /sample-buildout/var
    <BLANKLINE>
    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt

A blob_storage with a slash at the end can give unexpected results, creating a backup with name ``.0``.
See issue #26. So test what happens:

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage/
    ... """)
    >>> print system(buildout)
    Uninstalling backup.
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    <BLANKLINE>
    >>> print system('bin/backup')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups --quick --gzip
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/backups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups
    INFO: Renaming blobstorage.0 to blobstorage.1.
    INFO: rsync -a --delete --link-dest=../blobstorage.1 /sample-buildout/var/blobstorage /sample-buildout/var/blobstoragebackups/blobstorage.0
    <BLANKLINE>
