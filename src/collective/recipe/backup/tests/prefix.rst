# -*-doctest-*-

Locationprefix option
=====================

The locationprefix options allows you to set a base folder for all your backups and snapshot folders, instead of modifying all options in your recipe configuration.

Just to isolate some test differences, we run an empty buildout once::

    >>> ignore = system(buildout)

The simplest way to use it is to add a part in ``buildout.cfg`` like this::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... locationprefix = ${buildout:directory}/backuplocation
    ... """)

Let's run the buildout::

    >>> ignore = system(buildout)

Untested in this file, as it would create directories in your root or your
home dir, are absolute links (starting with a '/') or directories in your home
dir or relative (``../``) path. They do work, of course. Also ``~`` and
``$BACKUP``-style environment variables are expanded.


Backup
------

Calling ``bin/backup`` results in a normal repozo backup. We put in place a
mock repozo script that prints the options it is passed (and make it
executable). It is horridly unix-specific at the moment.

Some needed imports:

    >>> import sys
    >>> write('bin', 'repozo',
    ...       "#!%s\nimport sys\nprint ' '.join(sys.argv[1:])" % sys.executable)
    >>> dontcare = system('chmod u+x bin/repozo')

By default, backups are done in ``backuplocation/backups``::

    >>> print system('bin/backup')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/backuplocation/backups --quick --gzip
    INFO: Created /sample-buildout/backuplocation/backups
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/backuplocation/backups
    <BLANKLINE>

Full backups are placed there too::

    >>> print system('bin/fullbackup')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/backuplocation/backups -F --gzip
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/backuplocation/backups
    <BLANKLINE>


Restore
-------

You can restore the very latest backup with ``bin/restore``.
This will create the target directory when it does not exist::

    >>> ls('backuplocation')
    d  backups
    >>> print system('bin/restore', input='yes\n')
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/backuplocation/backups
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    Are you sure? (yes/No)?
    INFO: Created directory /sample-buildout/var/filestorage
    INFO: Please wait while restoring database file: /sample-buildout/backuplocation/backups to /sample-buildout/var/filestorage/Data.fs
    <BLANKLINE>
    >>> ls('backuplocation')
    d  backups
    >>> ls('var' , 'filestorage')

You can also restore the backup as of a certain date. Just pass a date
argument. According to repozo: specify UTC (not local) time.  The format is
``yyyy-mm-dd[-hh[-mm[-ss]]]``.

    >>> print system('bin/restore 1972-12-25', input='yes\n')
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/backuplocation/backups -D 1972-12-25
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    Are you sure? (yes/No)?
    INFO: Date restriction: restoring state at 1972-12-25.
    INFO: Please wait while restoring database file: /sample-buildout/backuplocation/backups to /sample-buildout/var/filestorage/Data.fs

Note that restoring a blobstorage to a specific date only works since
release 2.3.  We will test that a bit further on.


Snapshots
---------

For quickly grabbing the current state of a production database so you can
download it to your development laptop, you want a full backup. But
you shouldn't interfere with the regular backup regime. Likewise, a quick
backup just before updating the production server is a good idea. For that,
the ``bin/snapshotbackup`` is great. It places a full backup in, by default,
``var/snapshotbackups``.

    >>> print system('bin/snapshotbackup')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/backuplocation/snapshotbackups -F --gzip
    INFO: Created /sample-buildout/backuplocation/snapshotbackups
    INFO: Please wait while making snapshot backup: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/backuplocation/snapshotbackups
    <BLANKLINE>

You can restore the very latest snapshotbackup with ``bin/snapshotrestore``::

    >>> print system('bin/snapshotrestore', input='yes\n')
    --recover -o /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/backuplocation/snapshotbackups
    <BLANKLINE>
    This will replace the filestorage:
        /sample-buildout/var/filestorage/Data.fs
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-buildout/backuplocation/snapshotbackups to /sample-buildout/var/filestorage/Data.fs


Names of created scripts
------------------------

A backup part will normally be called ``[backup]``, leading to a
``bin/backup`` and ``bin/snapshotbackup``.  Should you name your part
something else,  the script names will also be different as will the created
``var/`` directories (since version 1.2):

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = plonebackup
    ...
    ... [plonebackup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... locationprefix = ${buildout:directory}/backuplocation
    ... """)
    >>> print system(buildout) # doctest:+ELLIPSIS
    Uninstalling backup.
    Installing plonebackup.
    Generated script '/sample-buildout/bin/plonebackup'.
    Generated script '/sample-buildout/bin/plonebackup-full'.
    Generated script '/sample-buildout/bin/plonebackup-snapshot'.
    Generated script '/sample-buildout/bin/plonebackup-restore'.
    Generated script '/sample-buildout/bin/plonebackup-snapshotrestore'.
    <BLANKLINE>

Note that the ``restore``, ``snapshotbackup`` and ``snapshotrestore`` script name used when the
name is ``[backup]`` is now prefixed with the part name:

    >>> ls('bin')
    -  buildout
    -  plonebackup
    -  plonebackup-full
    -  plonebackup-restore
    -  plonebackup-snapshot
    -  plonebackup-snapshotrestore
    -  repozo

In the backuplocation/ directory, the existing backups and snapshotbackups directories
are still present.  The recipe of course never removes that kind of directory!
The different part name *did* result in two directories named after the part:

    >>> ls('backuplocation')
    d  backups
    d  snapshotbackups

For the rest of the tests we use the ``[backup]`` name again.  And we clean up
the ``backuplocation/plonebackups`` and ``backuplocation/plonebackup-snaphots`` dirs:

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... locationprefix = ${buildout:directory}/backuplocation
    ... """)
    >>> dont_care = system(buildout) # doctest:+ELLIPSIS
