# -*-doctest-*-

Alternative restore sources
===========================

Create directories::

    >>> mkdir('alt')
    >>> mkdir('alt', 'data')
    >>> mkdir('alt', 'blobs')

You can restore from an alternative source.  Use case: first make a
backup of your production site, then go to the testing or staging
server and restore the production data there.  This is supported with
the ``alternative_restore_source`` option::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... alternative_restore_source =
    ...     Data ${buildout:directory}/alt/data
    ... """)
    >>> print(system(buildout))
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    Generated script '/sample-buildout/bin/altrestore'.
    <BLANKLINE>

Call the script::

    >>> print(system('bin/altrestore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    Are you sure? (yes/No)?
    INFO: Created directory /sample-buildout/var/filestorage
    INFO: Please wait while restoring database file: /sample-buildout/alt/data to /sample-buildout/var/filestorage/Data.fs
    >>> check_repozo_output()
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/alt/data

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
    ... alternative_restore_source =
    ...     Data ${buildout:directory}/alt/data
    ... """)
    >>> print(system(buildout))
    Uninstalling backup.
    Installing backup.
    While:
      Installing backup.
    Error: alternative_restore_source key 'Data' is missing a blobdir.
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
    ... alternative_restore_source =
    ...     Data ${buildout:directory}/alt/data ${buildout:directory}/alt/blobs
    ... """)
    >>> print(system(buildout))
    Installing backup.
    While:
      Installing backup.
    Error: alternative_restore_source key 'Data' specifies blobdir '/sample-buildout/alt/blobs' but the original storage has no blobstorage.
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
    ... alternative_restore_source =
    ...     Data ${buildout:directory}/alt/data ${buildout:directory}/alt/blobs
    ... """)
    >>> print(system(buildout))
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    Generated script '/sample-buildout/bin/altrestore'.
    <BLANKLINE>

Call the script::

    >>> ls('var')
    d  filestorage
    >>> remove('var', 'filestorage')
    >>> print(system('bin/altrestore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)? INFO: Created directory /sample-buildout/var/filestorage
    ERROR: There are no backups in /sample-buildout/alt/blobs.
    ERROR: Halting execution: restoring blobstorages would fail.
    <BLANKLINE>
    >>> ls('var')
    d  filestorage

Create the necessary sample directories and call the script again::

    >>> mkdir('alt', 'blobs', 'blobstorage.0')
    >>> mkdir('alt', 'blobs', 'blobstorage.0', 'blobstorage')
    >>> write('alt', 'blobs', 'blobstorage.0', 'blobstorage', 'blobfile.txt', 'Hello blob.')
    >>> print(system('bin/altrestore', input='yes\n'))
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
    >>> check_repozo_output()
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/alt/data
    >>> ls('var')
    d  blobstorage
    d  filestorage
    >>> ls('var', 'blobstorage')
    -   blobfile.txt
    >>> cat('var', 'blobstorage', 'blobfile.txt')
    Hello blob.

Calling the script with a specific date is supported just like the
normal restore script.  If the date is too early, the real repozo script would fail,
saying 'No files in repository before <date>'.  Our mock repozo script would accept it,
but we have added a check in the blob restore so we now fail as well.

    >>> print(system('bin/altrestore 2000-12-31-23-59', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Date restriction: restoring state at 2000-12-31-23-59.
    ERROR: Could not find backup of '2000-12-31-23-59' or earlier.
    ERROR: Halting execution: restoring blobstorages would fail.
    <BLANKLINE>

So test is with a date in the future::

    >>> print(system('bin/altrestore 2100-12-31-23-59', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Date restriction: restoring state at 2100-12-31-23-59.
    INFO: Please wait while restoring database file: /sample-buildout/alt/data to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/alt/blobs to /sample-buildout/var/blobstorage
    INFO: rsync -a  --delete /sample-buildout/alt/blobs/blobstorage.0/blobstorage /sample-buildout/var
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/alt/data -D 2100-12-31-23-59

When archive_blob is true, we use it::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... archive_blob = true
    ... alternative_restore_source =
    ...     Data ${buildout:directory}/alt/data ${buildout:directory}/alt/blobs
    ... """)
    >>> print(system(buildout))
    Uninstalling backup.
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    Generated script '/sample-buildout/bin/altrestore'.
    <BLANKLINE>
    >>> print(system('bin/backup'))
    INFO: Created /sample-buildout/var/backups
    INFO: Created /sample-buildout/var/blobstoragebackups
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/backups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragebackups
    INFO: tar cf /sample-buildout/var/blobstoragebackups/blobstorage.20....tar  -C /sample-buildout/var/blobstorage .
    INFO: Creating symlink from latest to blobstorage.20....tar
    >>> check_repozo_output()
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups --quick --gzip
    >>> remove('alt', 'data')
    >>> remove('alt', 'blobs')
    >>> print(system('mv var/backups alt/data'))
    >>> print(system('mv var/blobstoragebackups alt/blobs'))
    >>> print(system('bin/altrestore', input='yes\n'))
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
    INFO: Extracting /sample-buildout/alt/blobs/blobstorage.20....tar to /sample-buildout/var/blobstorage
    INFO: tar xf /sample-buildout/alt/blobs/blobstorage.20....tar  -C /sample-buildout/var/blobstorage
    >>> check_repozo_output()
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/alt/data
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
    ... alternative_restore_source =
    ...     Data ${buildout:directory}/alt/data
    ...
    ... [secondbackup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... alternative_restore_source =
    ...     Data ${buildout:directory}/alt/data
    ... """)
    >>> print(system(buildout))
    Uninstalling backup.
    Installing secondbackup.
    Generated script '/sample-buildout/bin/secondbackup'.
    Generated script '/sample-buildout/bin/secondbackup-snapshot'.
    Generated script '/sample-buildout/bin/secondbackup-restore'.
    Generated script '/sample-buildout/bin/secondbackup-snapshotrestore'.
    Generated script '/sample-buildout/bin/secondbackup-altrestore'.
    Installing firstbackup.
    Generated script '/sample-buildout/bin/firstbackup'.
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
    ... alternative_restore_source =
    ...     1 ${buildout:directory}/alt/data
    ... """)
    >>> print(system(buildout))
    Uninstalling firstbackup.
    Uninstalling secondbackup.
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    Generated script '/sample-buildout/bin/altrestore'.
    <BLANKLINE>
    >>> print(system('bin/altrestore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-buildout/alt/data to /sample-buildout/var/filestorage/Data.fs
    >>> check_repozo_output()
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/alt/data

Specifying both ``1`` and ``Data`` is bad.
But since version 5, only one line is supported anyway::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... alternative_restore_source =
    ...     1 ${buildout:directory}/alt/one
    ...     Data ${buildout:directory}/alt/data
    ... """)
    >>> print(system(buildout))
    Uninstalling backup.
    Installing backup.
    While:
      Installing backup.
    Error: Only one alternative_restore_source line is supported.

Unknown keys are bad::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... alternative_restore_source =
    ...     foo ${buildout:directory}/alt/foo
    ... """)
    >>> print(system(buildout))
    Installing backup.
    While:
      Installing backup.
    Error: alternative_restore_source key 'foo' unknown. Expected 1 or Data.

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
    ... alternative_restore_source =
    ...     Data
    ... """)
    >>> print(system(buildout))
    Installing backup.
    While:
      Installing backup.
    Error: alternative_restore_source line 'Data' has a wrong format. Should be: 'storage-name filestorage-backup-path', optionally followed by a blobstorage-backup-path.
