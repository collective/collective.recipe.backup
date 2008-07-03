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

Running the buildout adds a ``bin/backup`` and ``bin/snapshotbackup`` script
and, by default, the ``var/backups`` and ``var/snapshotbackups`` dir:

    >>> print system(buildout) # doctest:+ELLIPSIS
    Installing backup.
    backup: Created /sample-buildout/var/backups
    backup: Created /sample-buildout/var/snapshotbackups
    Getting distribution for 'zc.recipe.egg'.
    Got zc.recipe.egg 1.0.0.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    <BLANKLINE>
    >>> ls('var')
    d  backups
    d  snapshotbackups
    >>> ls('bin')
    -  backup
    -  buildout
    -  snapshotbackup

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

The recipe supports the following options:

location
    Location where backups are stored. Defaults to ``var/backups`` inside the
    buildout directory.

keep
    Number of full backups to keep. Defaults to ``0``, which means old backups
    are not removed. ``2``, for instance, means that the current and the
    previous full backup are kept. Older backups are removed, including their
    incremental backups.

datafs
    In case the ``Data.fs`` isn't in the default ``var/filestorage/Data.fs``
    location, this option can overwrite it.

full
    By default, incremental backups are made. If this option is set to 'true',
    bin/backup will always make a full backup.

debug
    In rare cases when you want to know exactly what's going on, set debug to
    'true' to get debug level logging.

snapshotlocation
    Location where snapshot defaults are stored. Defaults to
    ``var/snapshotbackups`` inside the buildout directory.

We'll use the three options.

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
    ... """)
    >>> print system(buildout) # doctest:+ELLIPSIS
    Uninstalling backup.
    Installing backup.
    backup: Created /sample-buildout/snap/my
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    <BLANKLINE>

Backups are now stored in ``/backups/myproject`` and the Data.fs location is
handled correctly despite being a relative link:

    >>> print system('bin/backup')
    --backup -f /sample-buildout/subfolder/myproject.fs -r /backups/myproject -F
    INFO: Backing up database file: ...

The same is true for the snapshot backup.

    >>> print system('bin/snapshotbackup')
    --backup -f /sample-buildout/subfolder/myproject.fs -r /sample-buildout/snap/my -F
    INFO: Making snapshot backup:...
