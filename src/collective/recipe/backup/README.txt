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
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups --gzip
    INFO: Backing up database file: ...


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
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/snapshotbackups -F --gzip
    INFO: Making snapshot backup:...


Names of created scripts
------------------------

A backup part will normally be called ``[backup]``, leading to a
``bin/backup`` and ``bin/snapshotbackup``.  Should you name your part
something else,  the script names will also be different as will the created
``var/`` directories (since version 1.2):

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = plonebackup
    ...
    ... [plonebackup]
    ... recipe = collective.recipe.backup
    ... """)
    >>> print system(buildout) # doctest:+ELLIPSIS
    Uninstalling backup.
    Installing plonebackup.
    backup: Created /sample-buildout/var/plonebackups
    backup: Created /sample-buildout/var/plonebackup-snapshots
    Generated script '/sample-buildout/bin/plonebackup'.
    Generated script '/sample-buildout/bin/plonebackup-snapshot'.
    Generated script '/sample-buildout/bin/plonebackup-restore'.

Note that the ``restore`` and ``snapshotbackup`` script name used when the
name is ``[backup]`` is now prefixed with the part name:

    >>> ls('bin')
    -  buildout
    -  plonebackup
    -  plonebackup-restore
    -  plonebackup-snapshot
    -  repozo

In the var/ directory, the existing backups and snapshotbackups directories
are still present.  The recipe of course never removes that kind of directory!
The different part name *did* result in two directories named after the part:

    >>> ls('var')
    d  backups
    d  plonebackup-snapshots
    d  plonebackups
    d  snapshotbackups

For the rest of the tests we use the ``[backup]`` name again.  And we clean up
the ``var/plonebackups`` and ``var/plonebackup-snaphots`` dirs:

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... """)
    >>> dont_care = system(buildout) # doctest:+ELLIPSIS
    >>> rmdir('var/plonebackups')
    >>> rmdir('var/plonebackup-snapshots')


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
    Use repozo's zipping functionality. 'true' by default. Set it to 'false'
    and repozo will notgzip its files. Note that gzipped databases are called
    ``*.fsz``, not ``*.fs.gz``. **Changed in 0.8**: the default used to be
    false, but it so totally makes sense to gzip your backups that we changed
    the default.

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
    ... keep = 2
    ... datafs = subfolder/myproject.fs
    ... full = true
    ... debug = true
    ... snapshotlocation = snap/my
    ... gzip = false
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
    --backup -f /sample-buildout/subfolder/myproject.fs -r /sample-buildout/myproject -F --verbose
    INFO: Backing up database file: ...

The same is true for the snapshot backup.

    >>> print system('bin/snapshotbackup')
    --backup -f /sample-buildout/subfolder/myproject.fs -r /sample-buildout/snap/my -F --verbose
    INFO: Making snapshot backup:...

Untested in this file, as it would create directories in your root or your
home dir, are absolute links (starting with a '/') or directories in your home
dir or relative (``../``) path. They do work, of course. Also ``~`` and
``$BACKUP``-style environment variables are expanded.


Cron job integration
====================

``bin/backup`` is of course ideal to put in your cronjob instead of a whole
``bin/repozo ....`` line. But you don't want the "INFO" level logging that you
get, as you'll get that in your mailbox. In your cronjob, just add ``-q`` or
``--quiet`` and ``bin/backup`` will shut up unless there's a problem.

    >>> print system('bin/backup -q')
    --backup -f /sample-buildout/subfolder/myproject.fs -r /sample-buildout/myproject -F --verbose
    >>> print system('bin/backup --quiet')
    --backup -f /sample-buildout/subfolder/myproject.fs -r /sample-buildout/myproject -F --verbose


In our case the ``--backup ...`` lines above are just the mock repozo script
that still prints something. So it proves that the command is executed, but it
won't end up in the output.

Speaking of cron jobs?  Take a look at `zc.recipe.usercrontab
<http://pypi.python.org/pypi/z3c.recipe.usercrontab>`_ if you want to handle
cronjobs from within your buildout.  For example::

    [backupcronjob]
    recipe = z3c.recipe.usercrontab
    times = 0 12 * * *
    command = ${buildout:directory}/bin/backup


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
same time with repozo. So they are not completely in sync. The "other"
databases are backed up first as a small difference in the catalog is just
mildly irritating, but the other way around users can get real errors::

    >>> print system('bin/backup')
    --backup -f /sample-buildout/var/filestorage/catalog.fs -r /sample-buildout/var/backups_catalog --gzip
    --backup -f /sample-buildout/var/filestorage/another.fs -r /sample-buildout/var/backups_another --gzip
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups --gzip
    INFO: Backing up database file: ...
    INFO: Backing up database file: ...
    INFO: Backing up database file: ...

Same with snapshot backups::

    >>> print system('bin/snapshotbackup')
    --backup -f /sample-buildout/var/filestorage/catalog.fs -r /sample-buildout/var/snapshotbackups_catalog -F --gzip
    --backup -f /sample-buildout/var/filestorage/another.fs -r /sample-buildout/var/snapshotbackups_another -F --gzip
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/snapshotbackups -F --gzip
    INFO: Making snapshot backup: ...
    INFO: Making snapshot backup: ...
    INFO: Making snapshot backup: ...

And a restore restores all three backups::

    >>> print system('bin/restore')
    --recover -o /sample-buildout/var/filestorage/catalog.fs -r /sample-buildout/var/backups_catalog
    --recover -o /sample-buildout/var/filestorage/another.fs -r /sample-buildout/var/backups_another
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups
    INFO: Restoring...
    INFO: Restoring...
    INFO: Restoring...

We fake three old backups in all the (snapshot)backup directories to
test if the 'keep' parameter is working correctly.

    >>> dirs = ('var/backups', 'var/snapshotbackups')
    >>> for tail in ('', '_catalog', '_another'):
    ...     for dir in dirs:
    ...         dir = dir + tail
    ...         for i in range(3):
    ...             write(dir, '%d.fs' % i, 'sample fs')
    >>> print system('bin/backup')
    --backup -f /sample-buildout/var/filestorage/catalog.fs -r /sample-buildout/var/backups_catalog --gzip
    --backup -f /sample-buildout/var/filestorage/another.fs -r /sample-buildout/var/backups_another --gzip
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups --gzip
    INFO: Backing up database file:...var/backups_catalog...
    INFO: Removed old backups, the latest 2 full backups have been kept.
    INFO: Backing up database file:...var/backups_another...
    INFO: Removed old backups, the latest 2 full backups have been kept.
    INFO: Backing up database file:...var/backups...
    INFO: Removed old backups, the latest 2 full backups have been kept.
    <BLANKLINE>

Now unfortunately if you would do "ls('var/backups')" here in the test
you would still see all three files; apparently buildout and the
system do not interact correctly here, as in real life the superfluous
backups are really gone.  So we will have to trust the above note that
old backups have been removed.

Same for the snapshot backups:

    >>> print system('bin/snapshotbackup')
    --backup -f /sample-buildout/var/filestorage/catalog.fs -r /sample-buildout/var/snapshotbackups_catalog -F --gzip
    --backup -f /sample-buildout/var/filestorage/another.fs -r /sample-buildout/var/snapshotbackups_another -F --gzip
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/snapshotbackups -F --gzip
    INFO: Making snapshot backup:...var/snapshotbackups_catalog...
    INFO: Removed old backups, the latest 2 full backups have been kept.
    INFO: Making snapshot backup:...var/snapshotbackups_another...
    INFO: Removed old backups, the latest 2 full backups have been kept.
    INFO: Making snapshot backup:...var/snapshotbackups...
    INFO: Removed old backups, the latest 2 full backups have been kept.
    <BLANKLINE>
