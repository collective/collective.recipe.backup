# -*-doctest-*-

Location
========

Just to isolate some test differences, we run an empty buildout once::

    >>> ignore = system(buildout)

Add mock ``bin/repozo`` script::

    >>> import sys
    >>> write('bin', 'repozo',
    ...       "#!%s\nimport sys\nprint ' '.join(sys.argv[1:])" % sys.executable)
    >>> dontcare = system('chmod u+x bin/repozo')

You should not mix backup locations; it is confusing for the recipe
(or at least its authors) when backups end up in the same directory::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... location = ${buildout:directory}/var/loc1
    ... blobbackuplocation = ${buildout:directory}/var/loc1
    ... snapshotlocation = ${buildout:directory}/var/loc2
    ... blobsnapshotlocation = ${buildout:directory}/var/loc2
    ... """)
    >>> print system('bin/buildout')
    While:
      Installing.
      Getting section backup.
      Initializing section backup.
    Error: These must be distinct locations:
    blobbackuplocation = /sample-buildout/var/loc1
    blobsnapshotlocation = /sample-buildout/var/loc2
    location = /sample-buildout/var/loc1
    snapshotlocation = /sample-buildout/var/loc2
    <BLANKLINE>

Some of these locations might be an empty string in some cases, which
is probably grudgingly allowed, at least by this particular check.

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... blob_storage = ${buildout:directory}/var/blobstorage
    ... enable_zipbackup = true
    ... location =
    ... blobbackuplocation =
    ... snapshotlocation =
    ... blobsnapshotlocation =
    ... ziplocation =
    ... blobziplocation =
    ... """)
    >>> print system('bin/buildout')
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/zipbackup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/ziprestore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    <BLANKLINE>


Unexisting backup location
--------------------------

The recipe tests the ``location`` option, to see if it will be able to
create folders when scripts are called.

We'll use all options, except the blob options for now::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... location = /my/unusable/path/for/backup
    ... """)
    >>> print system(buildout)
    Uninstalling backup.
    Installing backup.
    utils: WARNING: Not able to create /my/unusable/path/for/backup
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    <BLANKLINE>
