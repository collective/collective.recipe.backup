# -*-doctest-*-

zipbackup and ziprestore
========================

Since version 2.20, we can create a zipbackup and ziprestore
script.  These use a different backup location and have a few options
hardcoded: gzip and archive_blob are True, keep is 1, regardless of what
the options in the buildout recipe section are.  You can always create
a separate buildout section where you explicitly change this using
options for the standard bin/backup script.

By default the scripts are not created.  You can ensable the them by
setting the enable_zipbackup option to true.

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
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... # keep is ignored by the zipbackup script
    ... keep = 42
    ... enable_zipbackup = true
    ... """)
    >>> print system(buildout)
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
    INFO: tar cf /sample-buildout/var/blobstoragezips/blobstorage.0.tar -C /sample-buildout/var/blobstorage .
    <BLANKLINE>

Keep is ignored by zipbackup, always using 1 as value::

    >>> print system('bin/zipbackup')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/zipbackups -F --gzip
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/zipbackups
    INFO: Please wait while backing up blobs from /sample-buildout/var/blobstorage to /sample-buildout/var/blobstoragezips
    INFO: Renaming blobstorage.0.tar to blobstorage.1.tar.
    INFO: tar cf /sample-buildout/var/blobstoragezips/blobstorage.0.tar -C /sample-buildout/var/blobstorage .
    INFO: Removed 1 blob backup(s), the latest 1 backup(s) have been kept.
    <BLANKLINE>

Now test the ziprestore script::

    >>> print system('bin/ziprestore', input='yes\n')
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/zipbackups
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-buildout/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Created directory /sample-buildout/var/filestorage
    INFO: Please wait while restoring database file: /sample-buildout/var/zipbackups to /sample-buildout/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-buildout/var/blobstoragezips to /sample-buildout/var/blobstorage
    INFO: Removing /sample-buildout/var/blobstorage
    INFO: Extracting /sample-buildout/var/blobstoragezips/blobstorage.0.tar to /sample-buildout/var/blobstorage
    INFO: tar xf /sample-buildout/var/blobstoragezips/blobstorage.0.tar -C /sample-buildout/var/blobstorage
    <BLANKLINE>

You can choose not to enable the zip scripts::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... keep = 42
    ... enable_zipbackup = false
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
    -  backup
    -  buildout
    -  repozo
    -  restore
    -  snapshotbackup
    -  snapshotrestore

Or you simply do not list the enable_zipbackup option, falling back to
the default::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... keep = 42
    ... """)
    >>> print system(buildout)
    Uninstalling backup.
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    >>> ls('bin')
    -  backup
    -  buildout
    -  repozo
    -  restore
    -  snapshotbackup
    -  snapshotrestore

If backup_blobs is false, it is useless to enable the zipbackup, so we
refuse this combination::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... enable_zipbackup = true
    ... """)
    >>> print system(buildout)
    While:
      Installing.
      Getting section backup.
      Initializing section backup.
    Error: Cannot have backup_blobs false and enable_zipbackup true. zipbackup is useless without blobs.
