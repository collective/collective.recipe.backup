3.1 (2017-02-24)
================

- Add a ``locationprefix`` option to configure a folder where all other
  backup and snapshot folders will be created [erral]

- Only claim compatibility with Python 2.6 and 2.7.  [maurits]

- Updated test buildout to use most recent versions.  [maurits]


3.0.0 (2015-12-31)
==================

- Refactored the init and install methods of this recipe.  During the
  init phase we were reading the buildout configuration, but during
  this phase the configuration is still being build.  So differences
  could occur, especially in the order of execution of parts.  This
  was not good.  Most code is now moved from the init to the install
  (and update) method.  This has less possible problems.  Downside:
  some configuration errors are caught later.
  [maurits]

- Read ``zeo-var``, ``var``, ``file-storage`` from buildout sections.
  Update default backup and Data.fs locations based on this.
  [maurits]


2.22 (2015-12-30)
=================

- Do not accept ``backup_blobs`` false and ``enable_zipbackup`` true.
  The zipbackup script is useless without blobs.
  [maurits]

- Set default ``backup_blobs`` to true on Python 2.6 (Plone 4) and
  higher.  Otherwise false.  If no ``blob_storage`` can be found, we
  quit with an error.
  [maurits]

- Accept ``true``, ``yes``, ``on``, ``1``, in lower, upper or mixed
  case as true value.  Treat all other values in the buildout options
  as false.
  [maurits]

- Find plone.recipe.zope2instance recipes also when they are not
  completely lower case.  The zope2instance recipe itself works fine
  when it has mixed case, so we should accept this too.
  [maurits]


2.21 (2015-10-06)
=================

- When restoring, create ``var/filestorage`` if needed.
  Fixes #23.
  [maurits]


2.20 (2014-11-11)
=================

- Add ``enable_fullbackup`` option.  Default: true, so no change
  compared to previous version.
  [maurits]

- Create backup/snapshot/zipbackup directories only when needed.
  Running the backup script should not create the snapshot
  directories.
  [maurits]

- Add zipbackup and ziprestore scripts when ``enable_zipbackup = true``.
  [maurits]


2.19 (2014-06-16)
=================

- Call repozo with ``--quick`` when making an incremental backup.
  This is a lot faster.  Theoretically it lead to inconsistency if
  someone is messing in your backup directory.  You can return to the
  previous behavior by specifying ``quick = false`` in the backup
  recipe part in your buildout config.
  [maurits]

- check and create folders now happens after pre_commands is run
  [@djay]


2.18 (2014-04-29)
=================

- Add ``rsync_options`` option.  These are added to the default
  ``rsync -a`` command. Default is no extra parameters. This can be
  useful for example when you want to restore a backup from a
  symlinked directory, in which case ``rsync_options = --no-l -k``
  does the trick.
  [fiterbek]



2.17 (2014-02-07)
=================

- Add ``alternative_restore_sources`` option.  This creates a
  ``bin/altrestore`` script that restores from an alternative backup
  location, specified by that option.  You can use this to restore a
  backup of the production data to your testing or staging server.
  [maurits]

- When checking if the backup script will be able to create a path,
  remove all created directories.  Until now, only the final directory
  was removed, and not any created parent directories.
  [maurits]

- Testing: split the single big doctest file into multiple files, to
  make the automated tests less dependent on one another, making it
  easier to change them and add new ones.
  [maurits]

- No longer test with Python 2.4, because Travis does not support it
  out of the box.  Should still work fine.
  [maurits]


2.16 (2014-01-14)
=================

- Do not create blob backup dirs when not backing up blobs.
  Do not create filestorage backup dirs when not backing up filestorage.
  Fixes https://github.com/collective/collective.recipe.backup/issues/17
  [maurits]


2.15 (2013-09-16)
=================

- Restore compatibility with Python 2.4 (Plone 3).
  [maurits]


2.14 (2013-09-09)
=================

- Archive blob backups with buildout option ``gzip_blob``.
  [matejc]


2.13 (2013-07-15)
=================

- When printing that we halt the execution due to an error running
  repozo, actually halt the execution.
  [maurits]


2.12 (2013-06-28)
=================

- Backup directories are now created when we launch ``backup`` or
  ``fullbackup`` or ``snapshotbackup`` scripts, no more during
  initialization.
  [bsuttor]


2.11 (2013-05-06)
=================

- Print the names of filestorages and blobstorages that will be
  restored.  Issue #8.
  [maurits]

- Added a new command-line argument : ``--no-prompt`` disables user
  input when restoring a backup or snapshot. Useful for shell scripts.
  [bouchardsyl]

- Fixed command-line behavior with many arguments and not only a date.
  [bouchardsyl]


2.10 (2013-03-30)
=================

- Added ``fullbackup`` script that defaults to ``full=true``.  This
  could have been handled by making a new part, but it seemed like
  overkill to have to generate a complete new set of backup scripts,
  just to get one for full.
  [spanky]


2.9 (2013-03-06)
================

- Fixed possible KeyError: ``blob_snapshot_location``.
  [gforcada]



2.8 (2012-11-13)
================

- Fixed possible KeyError: ``blob_backup_location``.
  https://github.com/collective/collective.recipe.backup/issues/3
  [maurits]


2.7 (2012-09-27)
================

- additional_filestorages improved: blob support and custom location.
  [mamico]


2.6 (2012-08-29)
================

- Added pre_command and post_command options.  See the documentation.
  [maurits]


2.5 (2012-08-08)
================

- Moved code to github:
  https://github.com/collective/collective.recipe.backup
  [maurits]


2.4 (2011-12-20)
================

- Fixed silly indentation error that prevented old blob backups from
  being deleted when older than ``keep_blob_days`` days.
  [maurits]


2.3 (2011-10-05)
================

- Quit the rest of the backup or restore when a repozo call gives an
  error.  Main use case: when restoring to a specific date repozo will
  quit with an error when no files can be found, so we should also not
  try to restore blobs then.
  [maurits]

- Allow restoring the blobs to the specified date as well.
  [maurits]


2.2 (2011-09-14)
================

- Refactored script generation to make a split between initialization
  code and script arguments.  This restores compatibility with
  zc.buildout 1.5 for system pythons.  Actually we no longer create so
  called 'site package safe scripts' but just normal scripts that work
  for all zc.buildout versions.
  [maurits]

- Added option ``keep_blob_days``, which by default specifies that
  only for partial backups we keep 14 days of backups.  See the
  documentation.
  [maurits]

- Remove old blob backups when doing a snapshot backup.
  [maurits]


2.1 (2011-09-01)
================

- Raise an error when the four backup location options
  (blobbackuplocation, blobsnapshotlocation, location and
  snapshotlocation) are not four distinct locations (or empty
  strings).
  [maurits]

- Fixed possible TypeError: 'Option values must be strings'.
  Found by Alex Clark, thanks.
  [maurits]


2.0 (2011-08-26)
================

- Backup and restore blobs, using rsync.
  [maurits]

- Ask if the user is sure before doing a restore.
  [maurits]


1.7 (2010-12-10)
================

- Fix generated repozo commands to work also
  when recipe is configured to have a non **Data.fs**
  main db plus additional filestorages.
  e.g.:
  datafs= var/filestorage/main.fs
  additional = catalog
  [hplocher]


1.6 (2010-09-21)
================

- Added the option enable_snapshotrestore so that the creation of the
  script can be removed. Backwards compatible, if you don't specify it
  the script will still be created. Rationale: you may not want this
  script in a production buildout where mistakenly using
  snapshotrestore instead of snapshotbackup could hurt.
  [fredvd]


1.5 (2010-09-08)
================

- Fix: when running buildout with a config in a separate directory
  (like ``bin/buildout -c conf/prod.cfg``) the default backup
  directories are no longer created inside that separate directory.
  If you previously manually specified one of the location,
  snapshotlocation, or datafs parameters to work around this, you can
  probably remove those lines.  So: slightly saner defaults.
  [maurits]


1.4 (2010-08-06)
================

- Added documentation about how to get the required bin/repozo script
  in your buildout if for some reason you do not have it yet (like on
  Plone 4 when you do not have a zeo setup).
  Thanks to Vincent Fretin for the extra buildout lines.
  [maurits]


1.3 (2009-12-08)
================

- Added snapshotrestore script.  [Nejc Zupan]


1.2 (2009-10-26)
================

- The part name is now reflected in the created scripts and var/ directories.
  Originally bin/backup, bin/snapshotbackup, bin/restore and var/backups
  plus var/snapshotbackups were hardcoded.  Those are still there when you
  name your part ``[backup]``.  With a part named ``[NAME]``, you get
  bin/NAME, bin/NAME-snapshot, bin/NAME-restore and var/NAMEs plus
  var/NAME-snapshots.  Request by aclark for plone.org.  [reinout]


1.1 (2009-08-21)
================

- Run the cleanup script (removing too old backups that we no longer
  want to keep) for additional file storages as well.
  Fixes https://bugs.launchpad.net/collective.buildout/+bug/408224
  [maurits]

- Moved everything into a src/ subdirectory to ease testing on buildbot (which
  would grab all egss in the eggs/ dir that buildbot's mechanism creates.
  [reinout]


1.0 (2009-02-06)
================

- Quote all paths and arguments so that it works on paths that contain
  spaces (specially on Windows). [sidnei]


0.9 (2008-12-05)
================

- Windows path compatibility fix.  [Juan A. Diaz]


0.8 (2008-09-23)
================

- Changed the default for gzipping to True. Adding ``gzip = true`` to all our
  server deployment configs gets tired pretty quickly, so doing it by default
  is the best default. Stuff like this needs to be changed **before** a 1.0
  release :-) [reinout]

- Backup of additional databases (if you have configured them) now takes place
  before the backup of the main database (same with restore). [reinout]


0.7 (2008-09-19)
================

- Added $BACKUP-style enviroment variable subsitution in addition to the tilde
  expansion offered by 0.6. [reinout, idea by Fred van Dijk]


0.6 (2008-09-19)
================

- Fixed the test setup so both bin/test and python setup.py test
  work. [reinout+maurits]

- Added support for ~ in path names. And fixed a bug at the same time that
  would occur if you call the backup script from a different location than
  your buildout directory in combination with a non-absolute backup
  location. [reinout]


0.5 (2008-09-18)
================

- Added support for additional_filestorages option, needed for for instance a
  split-out catalog.fs. [reinout]

- Test setup fixes. [reinout+maurits]


0.4 (2008-08-19)
================

- Allowed the user to make the script more quiet (say in a cronjob)
  by using 'bin/backup -q' (or --quiet).  [maurits]

- Refactored initialization template so it is easier to change.  [maurits]


0.3.1 (2008-07-04)
==================

- Added 'gzip' option, including changes to the cleanup functionality that
  treats .fsz also as a full backup like .fs. [reinout]

- Fixed typo: repoze is now repozo everywhere... [reinout]


0.2 (2008-07-03)
================

- Extra tests and documentation change for 'keep': the default is to keep 2
  backups instead of all backups. [reinout]

- If debug=true, then repozo is also run in --verbose mode. [reinout]


0.1 (2008-07-03)
================

- Added bin/restore. [reinout]

- Added snapshot backups. [reinout]

- Enabled cleaning up of older backups. [reinout]

- First working version that runs repozo and that creates a backup dir if
  needed. [reinout]

- Started project based on zopeskel template. [reinout]
