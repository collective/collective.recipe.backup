# -*-doctest-*-

Supported options
=================

Just to isolate some test differences, we run an empty buildout once::

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
    ... enable_snapshotrestore = true
    ... pre_command = echo 'Can I have a backup?' > pre
    ... post_command =
    ...     echo 'Thanks a lot for the backup.' > post
    ...     echo 'We are done.' >> post
    ... """)
    >>> print(system(buildout))
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
    >>> print(output)
    <BLANKLINE>
    20...-...-... INFO: Created /sample-buildout/myproject
    20...-...-... INFO: Please wait while backing up database file: /sample-buildout/subfolder/myproject.fs to /sample-buildout/myproject
    20...-...-...
    >>> check_repozo_output()
    --backup -f /sample-buildout/subfolder/myproject.fs -r /sample-buildout/myproject -F --verbose --gzip

We do not check that the pre and post output appear in the correct order.
In the tests the output order can differ between Python 2 and 3.

    >>> cat('pre')
    Can I have a backup?
    >>> cat('post')
    Thanks a lot for the backup.
    We are done.
    >>> remove('pre')
    >>> remove('post')

We explicitly look for errors here::

    >>> if 'ERROR' in output: print(output)

The same is true for the snapshot backup.

    >>> output = system('bin/snapshotbackup')
    >>> print(output)
    20...-...-... INFO: Created /sample-buildout/var/snap/my
    20...-...-... INFO: Please wait while making snapshot backup: /sample-buildout/subfolder/myproject.fs to /sample-buildout/var/snap/my
    20...-...-...
    >>> if 'ERROR' in output: print(output)
    >>> check_repozo_output()
    --backup -f /sample-buildout/subfolder/myproject.fs -r /sample-buildout/var/snap/my -F --verbose --gzip
    >>> cat('pre')
    Can I have a backup?
    >>> cat('post')
    Thanks a lot for the backup.
    We are done.
    >>> remove('pre')
    >>> remove('post')

Untested in this file, as it would create directories in your root or your
home dir, are absolute links (starting with a '/') or directories in your home
dir or relative (``../``) path. They do work, of course. Also ``~`` and
``$BACKUP``-style environment variables are expanded.


Cron job integration
--------------------

``bin/backup`` is of course ideal to put in your cronjob instead of a whole
``bin/repozo ....`` line. But you don't want the 'INFO' level logging that you
get, as you'll get that in your mailbox. In your cronjob, just add ``-q`` or
``--quiet`` and ``bin/backup`` will shut up unless there's a problem.

In the tests, we do get messages unfortunately, though at least the
INFO level logging is not there::

    >>> print(system('bin/backup -q'))
    >>> cat('pre')
    Can I have a backup?
    >>> cat('post')
    Thanks a lot for the backup.
    We are done.
    >>> remove('pre')
    >>> remove('post')
    >>> check_repozo_output()
    --backup -f /sample-buildout/subfolder/myproject.fs -r /sample-buildout/myproject -F --verbose --gzip
    >>> print(system('bin/backup --quiet'))
    >>> cat('pre')
    Can I have a backup?
    >>> cat('post')
    Thanks a lot for the backup.
    We are done.
    >>> remove('pre')
    >>> remove('post')
    >>> check_repozo_output()
    --backup -f /sample-buildout/subfolder/myproject.fs -r /sample-buildout/myproject -F --verbose --gzip

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

    >>> print(system(buildout))
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
