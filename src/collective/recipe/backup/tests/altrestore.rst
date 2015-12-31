# -*-doctest-*-

Alternative restore sources
===========================

Just to isolate some test differences, we run an empty buildout once::

    >>> ignore = system(buildout)

Add mock ``bin/repozo`` script::

    >>> import sys
    >>> write('bin', 'repozo',
    ...       "#!%s\nimport sys\nprint ' '.join(sys.argv[1:])" % sys.executable)
    >>> dontcare = system('chmod u+x bin/repozo')

Create directories::

    >>> mkdir('var')
    >>> mkdir('alt')
    >>> mkdir('alt', 'data')
    >>> mkdir('alt', 'blobs')

You can restore from an alternative source.  Use case: first make a
backup of your production site, then go to the testing or staging
server and restore the production data there.  This is supported with
the ``alternative_restore_sources`` option::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... alternative_restore_sources =
    ...     Data ${buildout:directory}/alt/data
    ... """)
    >>> print system(buildout) # doctest:+ELLIPSIS
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/fullbackup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    Generated script '/sample-buildout/bin/altrestore'.
    <BLANKLINE>

Call the script::

    >>> print system('bin/altrestore', input='yes\n')  # doctest:+ELLIPSIS
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/alt/data
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    Are you sure? (yes/No)?
    INFO: Created directory /sample-buildout/var/filestorage
    INFO: Please wait while restoring database file: /sample-buildout/alt/data to /sample-buildout/var/filestorage/Data.fs

Add original blobstorage (usually done by having a part that creates a
zope instance or a zeoserver, but we do it simpler here) but forget to
add it to the alternative::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... alternative_restore_sources =
    ...     Data ${buildout:directory}/alt/data
    ... """)
    >>> print system(buildout) # doctest:+ELLIPSIS
    Uninstalling backup.
    Installing backup.
    While:
      Installing backup.
    Error: alternative_restore_sources key 'Data' is missing a blobdir.
    <BLANKLINE>

Add blobstorage to the alternative, but not the original::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... alternative_restore_sources =
    ...     Data ${buildout:directory}/alt/data ${buildout:directory}/alt/blobs
    ... """)
    >>> print system(buildout) # doctest:+ELLIPSIS
    Installing backup.
    While:
      Installing backup.
    Error: alternative_restore_sources key 'Data' specifies blobdir '/sample-buildout/alt/blobs' but the original storage has no blobstorage.
    <BLANKLINE>

Add blobstorage to original and alternative::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... alternative_restore_sources =
    ...     Data ${buildout:directory}/alt/data ${buildout:directory}/alt/blobs
    ... """)
    >>> print system(buildout) # doctest:+ELLIPSIS
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/fullbackup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    Generated script '/sample-buildout/bin/altrestore'.
    <BLANKLINE>

Call the script::

    >>> ls('var')
    d  filestorage
    >>> remove('var', 'filestorage')
    >>> print system('bin/altrestore', input='yes\n')  # doctest:+ELLIPSIS
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/alt/data
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    rsync: ...No such file or directory...
    INFO: Please wait while restoring database file: /sample-buildout/alt/data to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/alt/blobs to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/alt/blobs/blobstorage.0/blobstorage /sample-buildout/var
    <BLANKLINE>
    >>> ls('var')
    d  filestorage

Note that the rsync error is printed before the line that actually
calls rsync, but that is a strangeness in how ``stdout`` and
``stderr`` is combined in the tests.

Create the necessary sample directories and call the script again::

    >>> mkdir('alt', 'blobs', 'blobstorage.0')
    >>> mkdir('alt', 'blobs', 'blobstorage.0', 'blobstorage')
    >>> write('alt', 'blobs', 'blobstorage.0', 'blobstorage', 'blobfile.txt', 'Hello blob.')
    >>> print system('bin/altrestore', input='yes\n')  # doctest:+ELLIPSIS
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/alt/data
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-buildout/alt/data to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/alt/blobs to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/alt/blobs/blobstorage.0/blobstorage /sample-buildout/var
    <BLANKLINE>
    >>> ls('var')
    d  blobstorage
    d  filestorage
    >>> ls('var', 'blobstorage')
    -   blobfile.txt
    >>> cat('var', 'blobstorage', 'blobfile.txt')
    Hello blob.

Calling the script with a specific date is supported just like the
normal restore script::

    >>> print system('bin/altrestore 2000-12-31-23-59', input='yes\n')  # doctest:+ELLIPSIS
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/alt/data -D 2000-12-31-23-59
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Date restriction: restoring state at 2000-12-31-23-59.
    INFO: Please wait while restoring database file: /sample-buildout/alt/data to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/alt/blobs to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/alt/blobs/blobstorage.0/blobstorage /sample-buildout/var
    <BLANKLINE>

Test in combination with additional filestorage::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... additional_filestorages =
    ...     foo ${buildout:directory}/var/filestorage/foo/foo.fs ${buildout:directory}/var/blobstorage-foo
    ...     bar ${buildout:directory}/var/filestorage/bar/bar.fs
    ... alternative_restore_sources =
    ...     Data ${buildout:directory}/alt/data ${buildout:directory}/alt/blobs
    ...     foo ${buildout:directory}/alt/foo ${buildout:directory}/alt/fooblobs
    ...     bar ${buildout:directory}/alt/bar
    ... """)
    >>> remove('var')
    >>> mkdir('var')
    >>> mkdir('alt', 'foo')
    >>> mkdir('alt', 'bar')
    >>> mkdir('alt', 'fooblobs')
    >>> mkdir('alt', 'fooblobs', 'blobstorage-foo.0')
    >>> mkdir('alt', 'fooblobs', 'blobstorage-foo.0', 'blobstorage-foo')
    >>> write('alt', 'fooblobs', 'blobstorage-foo.0', 'blobstorage-foo', 'fooblobfile.txt', 'Hello fooblob.')
    >>> print system(buildout) # doctest:+ELLIPSIS
    Uninstalling backup.
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/fullbackup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    Generated script '/sample-buildout/bin/altrestore'.
    <BLANKLINE>
    >>> print system('bin/altrestore', input='yes\n')  # doctest:+ELLIPSIS
    --recover -o /sample-buildout/var/filestorage/foo/foo.fs -r /sample-buildout/alt/foo
    --recover -o /sample-buildout/var/filestorage/bar/bar.fs -r /sample-buildout/alt/bar
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/alt/data
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/foo/foo.fs
        /sample-buildout/var/filestorage/bar/bar.fs
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage-foo
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Created directory /sample-buildout/var/filestorage/foo
    INFO: Please wait while restoring database file: /sample-buildout/alt/foo to /sample-buildout/var/filestorage/foo/foo.fs
    INFO: Created directory /sample-buildout/var/filestorage/bar
    INFO: Please wait while restoring database file: /sample-buildout/alt/bar to /sample-buildout/var/filestorage/bar/bar.fs
    INFO: Please wait while restoring database file: /sample-buildout/alt/data to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/alt/fooblobs to /sample-buildout/var/blobstorage-foo
    INFO: rsync -a  --delete /sample-buildout/alt/fooblobs/blobstorage-foo.0/blobstorage-foo /sample-buildout/var
    INFO: No blob dir defined for bar storage
    INFO: Restoring blobs from /sample-buildout/alt/blobs to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/alt/blobs/blobstorage.0/blobstorage /sample-buildout/var
    <BLANKLINE>
    >>> ls('var')
    d  blobstorage
    d  blobstorage-foo
    d  filestorage
    >>> ls('var', 'blobstorage')
    -   blobfile.txt
    >>> cat('var', 'blobstorage', 'blobfile.txt')
    Hello blob.
    >>> ls('var', 'blobstorage-foo')
    -   fooblobfile.txt
    >>> cat('var', 'blobstorage-foo', 'fooblobfile.txt')
    Hello fooblob.

When gzip_blob is true, we use it::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... gzip_blob = true
    ... alternative_restore_sources =
    ...     Data ${buildout:directory}/alt/data ${buildout:directory}/alt/blobs
    ... """)
    >>> print system(buildout) # doctest:+ELLIPSIS
    Uninstalling backup.
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/fullbackup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    Generated script '/sample-buildout/bin/altrestore'.
    <BLANKLINE>
    >>> print system('bin/backup')  # doctest:+ELLIPSIS
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups --quick --gzip
    INFO: Created /sample-buildout/var/backups
    INFO: Created /sample-buildout/var/blobstoragebackups
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/backups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups
    INFO: tar czf /sample-buildout/var/blobstoragebackups/blobstorage.0.tar.gz -C /sample-buildout/var/blobstorage .
    >>> remove('alt', 'data')
    >>> remove('alt', 'blobs')
    >>> print system('mv var/backups alt/data')
    >>> print system('mv var/blobstoragebackups alt/blobs')
    >>> print system('bin/altrestore', input='yes\n')  # doctest:+ELLIPSIS
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/alt/data
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    <BLANKLINE>
    INFO: Please wait while restoring database file: /sample-buildout/alt/data to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/alt/blobs to /sample-buildout/var/blobstorage
    INFO: Removing /sample-buildout/var/blobstorage
    INFO: Extracting /sample-buildout/alt/blobs/blobstorage.0.tar.gz to /sample-buildout/var/blobstorage
    INFO: tar xzf /sample-buildout/alt/blobs/blobstorage.0.tar.gz -C /sample-buildout/var/blobstorage
    >>> ls('var', 'blobstorage')
    -   blobfile.txt

When the buildout part is not called ``backup``, we end up with
different names for the scripts::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts =
    ...     secondbackup
    ...     firstbackup
    ...
    ... [firstbackup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... alternative_restore_sources =
    ...     Data ${buildout:directory}/alt/data
    ...
    ... [secondbackup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... alternative_restore_sources =
    ...     Data ${buildout:directory}/alt/data
    ... """)
    >>> print system(buildout) # doctest:+ELLIPSIS
    Uninstalling backup.
    Installing secondbackup.
    Generated script '/sample-buildout/bin/secondbackup'.
    Generated script '/sample-buildout/bin/secondbackup-full'.
    Generated script '/sample-buildout/bin/secondbackup-snapshot'.
    Generated script '/sample-buildout/bin/secondbackup-restore'.
    Generated script '/sample-buildout/bin/secondbackup-snapshotrestore'.
    Generated script '/sample-buildout/bin/secondbackup-altrestore'.
    Installing firstbackup.
    Generated script '/sample-buildout/bin/firstbackup'.
    Generated script '/sample-buildout/bin/firstbackup-full'.
    Generated script '/sample-buildout/bin/firstbackup-snapshot'.
    Generated script '/sample-buildout/bin/firstbackup-restore'.
    Generated script '/sample-buildout/bin/firstbackup-snapshotrestore'.
    Generated script '/sample-buildout/bin/firstbackup-altrestore'.
    <BLANKLINE>


Corner cases
------------

Specifying ``1`` instead of ``Data`` is fine::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... alternative_restore_sources =
    ...     1 ${buildout:directory}/alt/data
    ... """)
    >>> print system(buildout) # doctest:+ELLIPSIS
    Uninstalling firstbackup.
    Uninstalling secondbackup.
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/fullbackup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    Generated script '/sample-buildout/bin/altrestore'.
    <BLANKLINE>
    >>> print system('bin/altrestore', input='yes\n')  # doctest:+ELLIPSIS
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/alt/data
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-buildout/alt/data to /sample-buildout/var/filestorage/Data.fs


Specifying both ``1`` and ``Data`` is bad::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... alternative_restore_sources =
    ...     1 ${buildout:directory}/alt/one
    ...     Data ${buildout:directory}/alt/data
    ... """)
    >>> print system(buildout) # doctest:+ELLIPSIS
    Uninstalling backup.
    Installing backup.
    While:
      Installing backup.
    Error: alternative_restore_sources key 'Data' is used. Are you using both '1' and 'Data'? They are alternative keys for the same Data.fs.

Switching them around also fails::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... alternative_restore_sources =
    ...     Data ${buildout:directory}/alt/data
    ...     1 ${buildout:directory}/alt/one
    ... """)
    >>> print system(buildout) # doctest:+ELLIPSIS
    Installing backup.
    While:
      Installing backup.
    Error: alternative_restore_sources key '1' is used. Are you using both '1' and 'Data'? They are alternative keys for the same Data.fs.

Missing keys is bad::

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
    ...     foo ${buildout:directory}/var/filestorage/foo/foo.fs
    ... alternative_restore_sources =
    ...     Data ${buildout:directory}/alt/data
    ... """)
    >>> print system(buildout) # doctest:+ELLIPSIS
    Installing backup.
    While:
      Installing backup.
    Error: alternative_restore_sources is missing key 'foo'.
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
    ...     foo ${buildout:directory}/var/filestorage/foo/foo.fs
    ... alternative_restore_sources =
    ...     foo ${buildout:directory}/alt/foo
    ... """)
    >>> print system(buildout) # doctest:+ELLIPSIS
    Installing backup.
    While:
      Installing backup.
    Error: alternative_restore_sources is missing key 'Data'.

Extra keys are also bad::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... alternative_restore_sources =
    ...     foo ${buildout:directory}/alt/foo
    ... """)
    >>> print system(buildout) # doctest:+ELLIPSIS
    Installing backup.
    While:
      Installing backup.
    Error: alternative_restore_sources key 'foo' unknown in storages.

A filestorage source path is required::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... alternative_restore_sources =
    ...     Data
    ... """)
    >>> print system(buildout) # doctest:+ELLIPSIS
    Installing backup.
    While:
      Installing backup.
    Error: alternative_restore_sources line 'Data' has a wrong format. Should be: 'storage-name filestorage-backup-path', optionally followed by a blobstorage-backup-path.
