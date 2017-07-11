# -*-doctest-*-

Blob storage
============

For tests with ``blob_timestamps = true``, see ``blob_timestamps.rst``.
That started as a copy of the current ``blobs.rst`` file.

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
    ... mailinglogger = 3.8.0
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

    >>> print(system('bin/buildout -t 5'))
    Setting socket time out to 5 seconds.
    Getting distribution for 'plone.recipe.zope2INSTANCE==3.9'...
    Got plone.recipe.zope2instance 3.9.
    Getting distribution for 'mailinglogger==3.8.0'...
    Got mailinglogger 3.8.0.
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
    ... mailinglogger = 3.8.0
    ...
    ... [instance]
    ... recipe = plone.recipe.zope2instance
    ... user = admin:admin
    ... var = ${buildout:directory}/var/another/
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... """)
    >>> print(system('bin/buildout'))
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
