Example usage
=============

Just to isolate some test differences, we run an empty buildout once::

    >>> ignore = system(buildout)

The simplest way to use it to add a part in ``buildout.cfg`` like this::

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
``var/snapshotbackups`` dirs::

    >>> print system(buildout) # doctest:+ELLIPSIS
    Installing backup.
    backup: Created /sample-buildout/var/backups
    backup: Created /sample-buildout/var/snapshotbackups
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

By default, backups are done in ``var/backups``::

    >>> print system('bin/backup')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups
    INFO: Backing up database file: ...

You can also tell the backup to be more quiet with ``--quiet`` or
``-q``.  That is useful at least for cronjobs.  Warnings or errors are
still shown.  In our case the mock repozo script still prints something::

    >>> print system('bin/backup --quiet')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups


Restore
-------

You can restore the very latest backup with ``bin/restore``::

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

additional_filestorages
    Advanced option, only needed when you have split for instance a
    ``catalog.fs`` out of the regular ``Data.fs``. Use it to specify the extra
    filestorages. (See explanation further on).


We'll use all options::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... location = ${buildout:directory}/myproject
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
    backup: Created /sample-buildout/myproject
    backup: Created /sample-buildout/snap/my
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    <BLANKLINE>

Backups are now stored in the ``/myproject`` folder inside buildout and the
Data.fs location is handled correctly despite not being an absolute path::

    >>> print system('bin/backup')
    --backup -f /sample-buildout/subfolder/myproject.fs -r /sample-buildout/myproject -F --verbose --gzip
    INFO: Backing up database file: ...

The same is true for the snapshot backup.

    >>> print system('bin/snapshotbackup')
    --backup -f /sample-buildout/subfolder/myproject.fs -r /sample-buildout/snap/my -F --verbose --gzip
    INFO: Making snapshot backup:...

Untested in this file, as it would create directories in your root or your
home dir, are absolute links (starting with a '/') or directories in your home
dir or relative (``../``) paths. They do work, of course.


Advanced usage: multiple Data.fs files
======================================

Sometimes, a Data.fs is split into several files. Most common reason is to
have a regular Data.fs and a catalog.fs which contains the
portal_catalog. This is supported with the ``additional_filestorages``
option::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... additional_filestorages =
    ...     catalog
    ...     another
    ... """)

The additional backups have to be stored separate from the ``Data.fs``
backup. That's done by appending the file's name and creating extra backup
directories named that way::

    >>> print system(buildout) # doctest:+ELLIPSIS
    Uninstalling backup.
    Installing backup.
    backup: Created /sample-buildout/var/backups_catalog
    backup: Created /sample-buildout/var/snapshotbackups_catalog
    backup: Created /sample-buildout/var/backups_another
    backup: Created /sample-buildout/var/snapshotbackups_another
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    <BLANKLINE>
    >>> ls('var')
    d  backups
    d  backups_another
    d  backups_catalog
    d  snapshotbackups
    d  snapshotbackups_another
    d  snapshotbackups_catalog

The various backups are done one after the other. They cannot be done at the
same time with repozo::

    >>> print system('bin/backup')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups
    --backup -f /sample-buildout/var/filestorage/catalog.fs -r /sample-buildout/var/backups_catalog
    --backup -f /sample-buildout/var/filestorage/another.fs -r /sample-buildout/var/backups_another
    INFO: Backing up database file: ...
    INFO: Backing up database file: ...
    INFO: Backing up database file: ...

Same with snapshot backups::

    >>> print system('bin/snapshotbackup')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/snapshotbackups -F
    --backup -f /sample-buildout/var/filestorage/catalog.fs -r /sample-buildout/var/snapshotbackups_catalog -F
    --backup -f /sample-buildout/var/filestorage/another.fs -r /sample-buildout/var/snapshotbackups_another -F
    INFO: Making snapshot backup: ...
    INFO: Making snapshot backup: ...
    INFO: Making snapshot backup: ...

And a restore restores all three backups::

    >>> print system('bin/restore')
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups
    --recover -o /sample-buildout/var/filestorage/catalog.fs -r /sample-buildout/var/backups_catalog
    --recover -o /sample-buildout/var/filestorage/another.fs -r /sample-buildout/var/backups_another
    INFO: Restoring...
    INFO: Restoring...
    INFO: Restoring...
