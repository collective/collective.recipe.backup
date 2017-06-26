# -*-doctest-*-

Supported options
=================

Just to isolate some test differences, we run an empty buildout once::

    >>> ignore = system(buildout)

Add mock ``bin/repozo`` script::

    >>> import sys
    >>> write('bin', 'repozo',
    ...       "#!%s\nimport sys\nprint ' '.join(sys.argv[1:])" % sys.executable)
    >>> dontcare = system('chmod u+x bin/repozo')

We'll use most options, except the blob options for now::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... location = ${buildout:directory}/myproject
    ... keep = 2
    ... datafs = subfolder/myproject.fs
    ... full = true
    ... debug = true
    ... snapshotlocation = snap/my
    ... gzip = false
    ... enable_snapshotrestore = true
    ... pre_command = echo 'Can I have a backup?'
    ... post_command =
    ...     echo 'Thanks a lot for the backup.'
    ...     echo 'We are done.'
    ... """)
    >>> print system(buildout)
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    <BLANKLINE>

Backups are now stored in the ``/myproject`` folder inside buildout
and the Data.fs location is handled correctly despite not being an
absolute path.  Note that the order in which the lines show up here in
the tests may be different from how they appear in reality.  This is
because several things conspire in the tests to mess up stdout and
stderr.  Anyway::

    >>> output = system('bin/backup')
    >>> print output
    --backup -f /sample-buildout/subfolder/myproject.fs -r /sample-buildout/myproject --quick -F --verbose
    Can I have a backup?
    <BLANKLINE>
    Thanks a lot for the backup.
    We are done.
    20...-...-... INFO: Created /sample-buildout/myproject
    20...-...-... INFO: Please wait while backing up database file: /sample-buildout/subfolder/myproject.fs to /sample-buildout/myproject
    20...-...-...

We explicitly look for errors here::

    >>> if 'ERROR' in output: print output

The same is true for the snapshot backup.

    >>> output = system('bin/snapshotbackup')
    >>> print output
    --backup -f /sample-buildout/subfolder/myproject.fs -r /sample-buildout/var/snap/my -F --verbose
    Can I have a backup?
    Thanks a lot for the backup.
    We are done.
    20...-...-... INFO: Created /sample-buildout/var/snap/my
    20...-...-... INFO: Please wait while making snapshot backup: /sample-buildout/subfolder/myproject.fs to /sample-buildout/var/snap/my
    20...-...-...
    >>> if 'ERROR' in output: print output

Untested in this file, as it would create directories in your root or your
home dir, are absolute links (starting with a '/') or directories in your home
dir or relative (``../``) path. They do work, of course. Also ``~`` and
``$BACKUP``-style environment variables are expanded.


Cron job integration
--------------------

``bin/backup`` is of course ideal to put in your cronjob instead of a whole
``bin/repozo ....`` line. But you don't want the "INFO" level logging that you
get, as you'll get that in your mailbox. In your cronjob, just add ``-q`` or
``--quiet`` and ``bin/backup`` will shut up unless there's a problem.

In the tests, we do get messages unfortunately, though at least the
INFO level logging is not there::

    >>> print system('bin/backup -q')
    --backup -f /sample-buildout/subfolder/myproject.fs -r /sample-buildout/myproject --quick -F --verbose
    Can I have a backup?
    Thanks a lot for the backup.
    We are done.
    >>> print system('bin/backup --quiet')
    --backup -f /sample-buildout/subfolder/myproject.fs -r /sample-buildout/myproject --quick -F --verbose
    Can I have a backup?
    Thanks a lot for the backup.
    We are done.

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


Disable the snapshotrestore script
----------------------------------

We generate a new buildout
with enable_snapshotrestore set to false. The script should not be
generated now (and buildout will actually remove the previously
generated script).

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... enable_snapshotrestore = false
    ... """)

    >>> print system(buildout)
    Uninstalling backup.
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    <BLANKLINE>
    >>> ls('bin')
    -  backup
    -  buildout
    -  repozo
    -  restore
    -  snapshotbackup


Not quick
---------

The repozo script has the quick option set the false by default.
Usually it makes sense to set it to true, as this can be a *lot*
quicker.  So version 2.19 introduced the quick option for the backup
script and has set the default to true.  You can set it to false if
wanted.

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... quick = false
    ... """)

    >>> print system(buildout)
    Uninstalling backup.
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    <BLANKLINE>
    >>> print system('bin/backup')
    --backup -f /sample-buildout/var/filestorage/Data.fs -r /sample-buildout/var/backups --gzip
    INFO: Created /sample-buildout/var/backups
    INFO: Please wait while backing up database file: /sample-buildout/var/filestorage/Data.fs to /sample-buildout/var/backups
    <BLANKLINE>


Enable the fullbackup script
----------------------------

We generate a new buildout with enable_fullbackup set to true.
This actually was the default before 4.0.
The fullbackup script should be generated now.

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... newest = false
    ... parts = backup
    ...
    ... [backup]
    ... recipe = collective.recipe.backup
    ... backup_blobs = false
    ... enable_fullbackup = true
    ... """)

    >>> print system(buildout)
    Uninstalling backup.
    Installing backup.
    Generated script '/sample-buildout/bin/backup'.
    Generated script '/sample-buildout/bin/fullbackup'.
    Generated script '/sample-buildout/bin/snapshotbackup'.
    Generated script '/sample-buildout/bin/restore'.
    Generated script '/sample-buildout/bin/snapshotrestore'.
    <BLANKLINE>
    >>> ls('bin')
    -  backup
    -  buildout
    -  fullbackup
    -  repozo
    -  restore
    -  snapshotbackup
    -  snapshotrestore
