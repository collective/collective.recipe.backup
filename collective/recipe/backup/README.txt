Example usage
=============

The simplest way to use it to add a part in ``buildout.cfg`` like this:

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... """)

Running the buildout adds a backup, snapshotbackup and restore scripts to the
``bin/`` directory and, by default, it creates the ``var/backups`` and
``var/snapshotbackups`` dirs:

    >>> print system(buildout) # doctest:+ELLIPSIS
    Installing backup.
    backup: Created /sample-buildout/var/backups
    backup: Created /sample-buildout/var/snapshotbackups
    Getting distribution for 'zc.recipe.egg'.
    Got zc.recipe.egg 1.0.0.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    <BLANKLINE>
    >>> ls('var')
    d  backups
    d  snapshotbackups
    >>> ls('bin')
    -  backup
    -  buildout
    -  restore
    -  snapshotbackup


Backup
------

Calling ``bin/backup`` results in a normal repozo backup. We put in place a
mock repozo script that prints the options it is passed (and make it
executable). It is horridly unix-specific at the moment.

    >>> import sys
    >>> write('bin', 'repozo',
    ...       "#!%s\nimport sys\nprint ' '.join(sys.argv[1:])" % sys.executable)
    >>> #write('bin', 'repozo', "#!/bin/sh\necho $*")
    >>> dontcare = system('chmod u+x bin/repozo')

By default, backups are done in ``var/backups``:

    >>> print system('bin/backup')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups
    INFO: Backing up database file: ...


Restore
-------

You can restore the very latest backup with ``bin/restore``:

    >>> print system('bin/restore')
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups
    INFO: Restoring...

You can also restore the backup as of a certain date. Just pass a date
argument. According to repozo: specify UTC (not local) time.  The format is
``yyyy-mm-dd[-hh[-mm[-ss]]]``.

    >>> print system('bin/restore 1972-12-25')
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups -D 1972-12-25
    INFO: Date restriction: restoring state at 1972-12-25.
    INFO: Restoring...


Snapshots
---------

For quickly grabbing the current state of a production database so you can
download it to your development laptop, you want a full backup. But
you shouldn't interfere with the regular backup regime. Likewise, a quick
backup just before updating the production server is a good idea. For that,
the ``bin/snapshotbackup`` is great. It places a full backup in, by default,
``var/snapshotbackups``.

    >>> print system('bin/snapshotbackup')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/snapshotbackups -F
    INFO: Making snapshot backup:...


Supported options
=================

The recipe supports the following options, none of which are needed by
default. The most common one to change is ``location``, as that allows you to
place your backups in some system-wide directory like
``/var/zopebackups/instancename/``.

location
    Location where backups are stored. Defaults to ``var/backups`` inside the
    buildout directory.

keep
    Number of full backups to keep. Defaults to ``2``, which means that the
    current and the previous full backup are kept. Older backups are removed,
    including their incremental backups. Set it to ``0`` to keep all backups.

datafs
    In case the ``Data.fs`` isn't in the default ``var/filestorage/Data.fs``
    location, this option can overwrite it.

full
    By default, incremental backups are made. If this option is set to 'true',
    bin/backup will always make a full backup.

debug
    In rare cases when you want to know exactly what's going on, set debug to
    'true' to get debug level logging of the recipe itself. Repozo is also run
    with ``--verbose`` if this option is enabled.

snapshotlocation
    Location where snapshot defaults are stored. Defaults to
    ``var/snapshotbackups`` inside the buildout directory.

gzip
    Use repozo's zipping functionality. 'false' by default. Set it to 'true'
    and repozo will gzip its files. Note that ``*.fs`` becomes ``*.fsz``, not
    ``*.fs.gz``.


We'll use all options:

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... location = /backups/myproject
    ... keep = 3
    ... datafs = subfolder/myproject.fs
    ... full = true
    ... debug = true
    ... snapshotlocation = snap/my
    ... gzip = true
    ... """)
    >>> print system(buildout) # doctest:+ELLIPSIS
    Uninstalling backup.
    Installing backup.
    backup: Created /sample-buildout/snap/my
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    <BLANKLINE>

Backups are now stored in ``/backups/myproject`` and the Data.fs location is
handled correctly despite being a relative link:

    >>> print system('bin/backup')
    --backup -f /sample-buildout/subfolder/myproject.fs -r /backups/myproject -F --verbose --gzip
    INFO: Backing up database file: ...

The same is true for the snapshot backup.

    >>> print system('bin/snapshotbackup')
    --backup -f /sample-buildout/subfolder/myproject.fs -r /sample-buildout/snap/my -F --verbose --gzip
    INFO: Making snapshot backup:...
