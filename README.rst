Easy Zope backup/restore recipe for buildout
********************************************

.. image:: https://travis-ci.org/collective/collective.recipe.backup.png
    :target: https://travis-ci.org/collective/collective.recipe.backup

.. contents::


Introduction
============

This recipe is mostly a wrapper around the ``bin/repozo`` script in
your Zope buildout.  It requires that this script is already made
available.  If this is not the case, you will get an error like this
when you run one of the scripts: ``bin/repozo: No such file or
directory``.  You should be fine when you are on Plone 3 or when you
are on Plone 4 and are using ``plone.recipe.zeoserver``.  If this is
not the case, the easiest way of getting a ``bin/repozo`` script is to
add a new section in your ``buildout.cfg`` (do not forget to add it in the
``parts`` directive)::

  [repozo]
  recipe = zc.recipe.egg
  eggs = ZODB3
  scripts = repozo

``bin/repozo`` is a Zope script to make backups of your ``Data.fs``.
Looking up the settings can be a chore. And you have to pick a
directory where to put the backups. This recipe provides **sensible
defaults** for your common backup tasks. Making backups a piece of
cake is important!

- ``bin/backup`` makes an incremental backup.

- ``bin/fullbackup`` always makes a full backup.

- ``bin/restore`` restores the latest backup.

- ``bin/snapshotbackup`` makes a full backup, separate from the
  regular backups. Handy for copying the current production database
  to your laptop or right before a big change in the site.


Development
===========

- Code repository: https://github.com/collective/collective.recipe.backup

- Small fixes are fine on master, for larger changes or if you are
  unsure, please create a branch or a pull request.

- The code comes with a ``buildout.cfg``.  Please bootstrap the
  buildout and run the created ``bin/test`` to see if the tests still
  pass.  Please try to add tests if you add code.

- The long description of this package (as shown on PyPI), used to
  contain a big file with lots of test code that showed how to use the
  recipe.  This grew too large, so we left it out.  It is probably
  still good reading if you are wondering about the effect some
  options have.  See ``src/collective/recipe/backup/README.txt``.

- Questions and comments to the Plone product-developers list or to
  mailto:maurits@vanrees.org and mailto:reinout@vanrees.org.


Example usage
=============

The simplest way to use this recipe is to add a part in ``buildout.cfg`` like this::

    [buildout]
    parts = backup
    
    [backup]
    recipe = collective.recipe.backup

You can set lots of extra options, but the recipe authors like to
think they have created sane defaults, so this single line stating the
recipe name should be enough in most cases.

Running the buildout adds the ``backup``, ``fullbackup``, ``snapshotbackup``,
``restore`` and ``snapshotrestore`` scripts to the ``bin/`` directory
of the buildout and, by default, it creates the ``var/backups`` and
``var/snapshotbackups`` directories in that same buildout.


Backed up data
==============

Which data does this recipe backup?

- The Zope Object DataBase (ZODB) filestorage, by default located at
  ``var/filestorage/Data.fs``.

- Possibly additional filestorages, see the
  ``additional_filestorages`` option.

- The blobstorage (since version 2.0) if your buildout uses it, by
  default located at ``var/blobstorage``.


Data that is *not* backed up
============================

Which data does this recipe *not* backup?  Everything else of course,
but specifically:

- Data stored in ``RelStorage`` will *not* be backed up.  (You could
  still use this recipe to back up the filesystem blobstorage,
  possibly with the ``only_blobs`` option.)

- Other data stored in SQL, perhaps via SQLAlchemy, will *not* be
  backed up.

- It does *not* create a backup of your entire buildout directory.


Is your backup backed up?
=========================

Note that the backups are by default created in the ``var`` directory
of the buildout, so if you accidentally remove the entire buildout,
you also lose your backups.  It should be standard practice to use the
``location`` option to specify a backup location in for example the
home directory of the user.  You should also arrange to copy that
backup to a different machine/country/continent/planet.


Backup
======

Calling ``bin/backup`` results in a normal incremental repozo backup
that creates a backup of the ``Data.fs`` in ``var/backups``.  When you
have a blob storage it is by default backed up to
``var/blobstoragebackups``.

Calling ``bin/fullbackup`` results in a normal FULL repozo backup
that creates a backup of the ``Data.fs`` in ``var/backups``.  When you
have a blob storage it is by default backed up to
``var/blobstoragebackups``.  This script is provided so that you can
set different cron jobs for full and incremental backups.  You may
want to have incrementals done daily, with full backups done weekly.
Now you can!

You should normally do a ``bin/zeopack`` regularly, say once a week,
to remove unused objects from your Zope ``Data.fs``.  The next time
``bin/backup`` is called, a complete fresh backup is made, because an
incremental backup is not possible anymore.  This is standard
``bin/repozo`` behaviour.


Snapshots
=========

For quickly grabbing the current state of a production database so you
can download it to your development laptop, you want a full backup.
But you shouldn't interfere with the regular backup regime.  Likewise,
a quick backup just before updating the production server is a good
idea.  For that, the ``bin/snapshotbackup`` is great. It places a full
backup in, by default, ``var/snapshotbackups``.


Restore
=======

Calling ``bin/restore`` restores the very latest normal incremental
``repozo`` backup and restores the blobstorage if you have that.

You can restore the very latest snapshotbackup with ``bin/snapshotrestore``.

You can also restore the backup as of a certain date. Just pass a date
argument. According to ``repozo``: specify UTC (not local) time.
The format is
``yyyy-mm-dd[-hh[-mm[-ss]]]``.  So as a simple example::

    bin/restore 1972-12-25

Since version 2.3 this also works for restoring blobs.  We simply
restore the directory from the first backup after the specified date.

Since version 2.0, the restore scripts ask for confirmation before
starting the restore, as this is a potentially dangerous command.
("Oops, I have restored the live site but I meant to restore the test
site.")  You need to explicitly type 'yes'::

    This will replace the filestorage (Data.fs).
    This will replace the blobstorage.
    Are you sure? (yes/No)?


Names of created scripts
========================

A backup part will normally be called ``[backup]``, leading to a
``bin/backup`` and ``bin/snapshotbackup``.  Should you name your part
something else,  the script names will also be different, as will the created
``var/`` directories (since version 1.2)::

    [buildout]
    parts = plonebackup
    
    [plonebackup]
    recipe = collective.recipe.backup

That buildout snippet will create these directories::

    var/plonebackups
    var/plonebackup-snapshots

and these scripts::

    bin/plonebackup
    bin/plonebackup-full
    bin/plonebackup-snapshot
    bin/plonebackup-restore
    bin/plonebackup-snapshotrestore


Supported options
=================

The recipe supports the following options, none of which are needed by
default. The most common ones to change are ``location`` and
``blobbackuplocation``, as those allow you to place your backups in
some system-wide directory like ``/var/zopebackups/instancename/`` and
``/var/zopebackups/instancename-blobs/``.

``location``
    Location where backups are stored. Defaults to ``var/backups`` inside the
    buildout directory.

``blobbackuplocation`` 
    Directory where the blob storage will be backed up to.  Defaults
    to ``var/blobstoragebackups`` inside the buildout directory.

``keep``
    Number of full backups to keep. Defaults to ``2``, which means that the
    current and the previous full backup are kept. Older backups are removed,
    including their incremental backups. Set it to ``0`` to keep all backups.

``keep_blob_days``
    Number of *days* of blob backups to keep.  Defaults to ``14``, so
    two weeks.  This is **only** used for partial (full=False)
    backups, so this is what gets used normally when you do a
    ``bin/backup``.  This option has been added in 2.2.  For full
    backups (snapshots) we just use the ``keep`` option.  Recommended
    is to keep these values in sync with how often you do a ``zeopack`` on
    the ``Data.fs``, according to the formula ``keep *
    days_between_zeopacks = keep_blob_days``.  The default matches one
    zeopack per seven days (``2*7=14``).

``datafs``
    In case the ``Data.fs`` isn't in the default ``var/filestorage/Data.fs``
    location, this option can overwrite it.

``full``
    By default, incremental backups are made. If this option is set to ``true``,
    ``bin/backup`` will always make a full backup.  This option is (obviously)
    the default when using the ``fullbackup`` script.

``debug``
    In rare cases when you want to know exactly what's going on, set debug to
    ``true`` to get debug level logging of the recipe itself. ``repozo`` is also run
    with ``--verbose`` if this option is enabled.

``snapshotlocation``
    Location where snapshot backups of the filestorage are stored. Defaults to
    ``var/snapshotbackups`` inside the buildout directory.

``gzip``
    Use repozo's zipping functionality. ``true`` by default. Set it to ``false``
    and repozo will not gzip its files. Note that gzipped databases are called
    ``*.fsz``, not ``*.fs.gz``. **Changed in 0.8**: the default used to be
    false, but it so totally makes sense to gzip your backups that we changed
    the default.

``additional_filestorages``
    Advanced option, only needed when you have split for instance a
    ``catalog.fs`` out of the regular ``Data.fs``.
    Use it to specify the extra
    filestorages. (See explanation further on).

``enable_snapshotrestore``
    Having a ``snapshotrestore`` script is very useful in development
    environments, but can be harmful in a production buildout. The
    script restores the latest snapshot directly to your filestorage
    and it used to do this without asking any questions whatsoever
    (this has been changed to require an explicit ``yes`` as answer).
    If you don't want a ``snapshotrestore`` script, set this option to false.

``blob_storage``
    Location of the directory where the blobs (binary large objects)
    are stored.  This is used in Plone 4 and higher, or on Plone 3 if
    you use ``plone.app.blob``.  This option is ignored if backup_blobs is
    ``false``.  The location is not set by default.  When there is a part
    using ``plone.recipe.zeoserver``, ``plone.recipe.zope2instance`` or
    ``plone.recipe.zope2zeoserver``, we check if that has a
    blob-storage option and use that as default.  Note that we pick
    the first one that has this option and we do not care about
    shared-blob settings, so there are probably corner cases where we
    do not make the best decision here.  Use this option to override
    it in that case.

``blob``-storage
    Alternative spelling for the preferred ``blob_storage``, as
    ``plone.recipe.zope2instance`` spells it as ``blob-storage`` and we are
    using underscores in all the other options.  Pick one.

``backup_blobs``
    Backup the blob storage.  This requires the ``blob_storage`` location
    to be set.  If no ``blob_storage`` location has been set and we cannot
    find one by looking in the other buildout parts, we default to
    ``False``, otherwise to ``True``.

``blobsnapshotlocation``
    Directory where the blob storage snapshots will be created.
    Defaults to ``var/blobstoragesnapshots`` inside the buildout
    directory.

``only_blobs``
    Only backup the blobstorage, not the ``Data.fs`` filestorage.  False
    by default.  May be a useful option if for example you want to
    create one ``bin/filestoragebackup`` script and one
    ``bin/blobstoragebackup`` script, using ``only_blobs`` in one and
    ``backup_blobs`` in the other.

``use_rsync``
    Use ``rsync`` with hard links for backing up the blobs.  Default is
    true.  ``rsync`` is probably not available on all machines though, and
    I guess hard links will not work on Windows.  When you set this to
    false, we fall back to a simple copy (``shutil.copytree`` from
    Python in fact).

``gzip_blob``
    Use `tar` archiving functionality. ``false`` by default. Set it to ``true``
    and backup/restore will be done with `tar` command. Note that `tar`
    commmand must be available on machine if this option is set to `true`.
    This option also works with snapshot backup/restore commands. As this
    counts as a full backup `keep_blob_days` is ignored.

``pre_command``
    Command to execute before starting the backup.  One use case would
    be to mount a remote file system using NFS or sshfs and put the
    backup there.  Any output will be printed.  If you do not like
    that, you can always redirect output somewhere else (``mycommand >
    /dev/null`` on Unix).  Refer to your local Unix guru for more
    information.  If the command fails, the backup script quits with
    an error.  You can specify multiple commands.

``post_command``
    Command to execute after the backup has finished.  One use case
    would be to unmount the remote file system that you mounted
    earlier using the ``pre_command``.  See that ``pre_command`` above for
    more info.


An example buildout snippet using most options, except the blob
options, would look like this::

    [backup]
    recipe = collective.recipe.backup
    location = ${buildout:directory}/myproject
    keep = 2
    datafs = subfolder/myproject.fs
    full = true
    debug = true
    snapshotlocation = snap/my
    gzip = false
    enable_snapshotrestore = true
    pre_command = echo 'Can I have a backup?'
    post_command =
        echo 'Thanks a lot for the backup.'
        echo 'We are done.'

Paths in directories or files can use relative (``../``) paths, and
``~`` (home dir) and ``$BACKUP``-style environment variables are
expanded.


Cron job integration
====================

``bin/backup`` is of course ideal to put in your cronjob instead of a whole
``bin/repozo ....`` line. But you don't want the "INFO" level logging that you
get, as you'll get that in your mailbox. In your cronjob, just add ``-q`` or
``--quiet`` and ``bin/backup`` will shut up unless there's a problem.

Speaking of cron jobs?  Take a look at `zc.recipe.usercrontab
<http://pypi.python.org/pypi/z3c.recipe.usercrontab>`_ if you want to handle
cronjobs from within your buildout.  For example::

    [backupcronjob]
    recipe = z3c.recipe.usercrontab
    times = 0 12 * * *
    command = ${buildout:directory}/bin/backup


Advanced usage: multiple Data.fs files
======================================

Sometimes, a filestorage is split into several files. Most common reason is to
have a regular ``Data.fs`` and a ``catalog.fs`` which contains the
``portal_catalog``. This is supported with the ``additional_filestorages``
option::

    [backup]
    recipe = collective.recipe.backup
    additional_filestorages =
        catalog
        another

This means that, with the standard ``Data.fs``, the ``bin/backup``
script will now backup three filestorages::

    var/filestorage/Data.fs
    var/filestorage/catalog.fs
    var/filestorage/another.fs

The additional backups have to be stored separate from the ``Data.fs``
backup. That's done by appending the file's name and creating extra backup
directories named that way::

    var/backups_catalog
    var/snapshotbackups_catalog
    var/backups_another
    var/snapshotbackups_another

The various backups are done one after the other. They cannot be done at the
same time with ``repozo``. So they are not completely in sync. The "other"
databases are backed up first as a small difference in the catalog is just
mildly irritating, but the other way around users can get real errors.

If you want more control of the filestorage source path, you can explicitly
set it (with or without the blobstorage path). For example::

    [backup]
    recipe = collective.recipe.backup
    additional_filestorages =
        foo ${buildout:directory}/var/filestorage/foo/foo.fs ${buildout:directory}/var/blobstorage-foo
        bar ${buildout:directory}/var/filestorage/bar/bar.fs

In the ``additional_filestorages`` option you can define different filestorage using
this syntax::

    additional_filestorages =
        storagename1 [datafs1_path [blobdir1]]
        storagename2 [datafs2_path [blobdir2]]

If the ``datafs_path`` is missing, then the default value will be used
(``var/filestorage/storagename1.fs``).  If you do not specify a
``blobdir``, then this means no blobs will be backed up for that
storage.  Note that if you specify ``blobdir`` you must specify
``datafs_path`` as well.

Note that ``collective.recipe.filestorage`` creates additional
filestorages in a slightly different location, but you can explictly define the
paths of filestorage and blobstorage for all the ``parts`` defined in the recipe.
Work is in progress to improve this.


Blob storage
============

New in this recipe (since version 2.0) is that we backup the blob
storage.  Plone 4 uses a blob storage to store files (Binary Large
OBjects) on the file system.  In Plone 3 this is optional.  When this
is used, it should be backed up of course.  You must specify the
source blob_storage directory where Plone (or Zope) stores its blobs.
As indicated earlier, when we do not set it specifically, we try to
get the location from other parts, for example the
``plone.recipe.zope2instance`` recipe::

    [buildout]
    parts = instance backup

    [instance]
    recipe = plone.recipe.zope2instance
    user = admin:admin
    blob-storage = ${buildout:directory}/var/somewhere

    [backup]
    recipe = collective.recipe.backup

If needed, we can tell buildout that we *only* want to backup blobs or
specifically do *not* want to backup the blobs.  Specifying this using
the ``backup_blobs`` and ``only_blobs`` options might be useful in
case you want to separate this into several scripts::

    [buildout]
    newest = false
    parts = filebackup blobbackup
    
    [filebackup]
    recipe = collective.recipe.backup
    backup_blobs = false
    
    [blobbackup]
    recipe = collective.recipe.backup
    blob_storage = ${buildout:directory}/var/blobstorage
    only_blobs = true

With this setup ``bin/filebackup`` now only backs up the filestorage
and ``bin/blobbackup`` only backs up the blobstorage.


rsync
=====

By default we use ``rsync`` to create backups.  We create hard links
with this tool, to save disk space and still have incremental backups.
This probably requires a unixy (Linux, Mac OS X) operating system.
It is based on this article by Mike Rubel:
http://www.mikerubel.org/computers/rsync_snapshots/

We have not tried this on Windows.  Reports are welcome, but best is
probably to set the ``use_rsync = false`` option in the backup part.
Then we simply copy the blobstorage directory.
