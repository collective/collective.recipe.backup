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

Running the buildout adds a ``bin/backup`` script and the ``var/backups`` dir:

    >>> print system(buildout) # doctest:+ELLIPSIS
    Installing backup.
    backup: Created /sample-buildout/var/backups
    Getting distribution for 'zc.recipe.egg'.
    Got zc.recipe.egg 1.0.0.
    Generated script '/sample-buildout/bin/backup'.
    <BLANKLINE>
    >>> ls('var')
    d  backups
    >>> ls('bin')
    -  backup
    -  buildout

Calling ``bin/backup`` results in a normal repozo backup. We'll put in place a
mock repozo script that prints the options it is passed.

    >>> write('bin', 'repozo', "#!python2.4\nimport sys\nprint sys.argv[1:]")
    >>> print system('bin/backup')
    >>> cat('bin', 'backup')