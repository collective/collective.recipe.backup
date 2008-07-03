# Wrapper that invokes repozo.
from operator import itemgetter
import logging
import os
import sys


logger = logging.getLogger('backup')


def backup_main(bin_dir, datafs, backup_location, keep, full):
    """Main method, gets called by generated bin/backup."""
    repozo = os.path.join(bin_dir, 'repozo')
    logger.info("Backing up database file: %s to %s...",
                datafs, backup_location)
    os.system(repozo + ' ' +
              backup_arguments(datafs, backup_location, full))
    logger.debug("Repoze command executed.")
    cleanup(backup_location, keep)


def snapshot_main(bin_dir, datafs, snapshot_location, keep):
    """Main method, gets called by generated bin/snapshotbackup."""
    repozo = os.path.join(bin_dir, 'repozo')
    logger.info("Making snapshot backup: %s to %s...",
                datafs, snapshot_location)
    os.system(repozo + ' ' +
              backup_arguments(datafs, snapshot_location, full=True))
    logger.debug("Repoze command executed.")
    cleanup(snapshot_location, keep)


def restore_main(bin_dir, datafs, backup_location):
    """Main method, gets called by generated bin/restore."""
    repozo = os.path.join(bin_dir, 'repozo')
    logger.debug("If things break: did you stop zope?")
    date = None
    if len(sys.argv) > 1:
        date = sys.argv[1]
        logger.debug("Argument passed to bin/restore, we assume it is "
                     "a date that we have to pass to repozo: %s.", date)
        logger.info("Date restriction: restoring state at %s." % date)
    logger.info("Restoring database file: %s to %s...",
                backup_location, datafs)
    os.system(repozo + ' ' +
              restore_arguments(datafs, backup_location, date))
    logger.debug("Repoze command executed.")


def backup_arguments(datafs=None,
                     backup_location=None,
                     full=False,
                     ):
    """
      >>> backup_arguments()
      Traceback (most recent call last):
      ...
      RuntimeError: Missing locations.
      >>> backup_arguments(datafs='in/Data.fs', backup_location='out')
      '--backup -f in/Data.fs -r out'
      >>> backup_arguments(datafs='in/Data.fs', backup_location='out', full=True)
      '--backup -f in/Data.fs -r out -F'

    """
    if datafs is None or backup_location is None:
        raise RuntimeError("Missing locations.")
    arguments = []
    arguments.append('--backup')
    arguments.append('-f %s' % datafs)
    arguments.append('-r %s' % backup_location)
    if full:
        # By default, there's an incremental backup, if possible.
        arguments.append('-F')
    else:
        logger.debug("You're not making a full backup. Note that if there "
                     "are no changes since the last backup, there won't "
                     "be a new incremental backup file.")
    args = ' '.join(arguments)
    logger.debug("Repoze arguments used: %s", args)
    return args


def restore_arguments(datafs=None,
                      backup_location=None,
                      date=None):
    """
      >>> restore_arguments()
      Traceback (most recent call last):
      ...
      RuntimeError: Missing locations.
      >>> restore_arguments(datafs='in/Data.fs', backup_location='out')
      '--recover -o in/Data.fs -r out'

    """
    if datafs is None or backup_location is None:
        raise RuntimeError("Missing locations.")
    arguments = []
    arguments.append('--recover')
    arguments.append('-o %s' % datafs)
    arguments.append('-r %s' % backup_location)
    if date is not None:
        logger.debug("Restore as of date %r requested.", date)
        arguments.append('-D %s' % date)
    args = ' '.join(arguments)
    logger.debug("Repoze arguments used: %s", args)
    return args


def cleanup(backup_location, keep=None):
    """Clean up old backups

    For the test, we create a backup dir using buildout's test support methods:

      >>> mkdir('back')
      >>> backup_dir = join('back')

    And we'll make a function that creates a backup file for us and that also
    sets the file modification dates to a meaningful time.

      >>> import time
      >>> import os
      >>> next_mod_time = time.time() - 1000
      >>> def add_backup(name):
      ...     global next_mod_time
      ...     write('back', name, 'dummycontents')
      ...     # Change modification time, every new file is 10 seconds older.
      ...     os.utime(join('back', name), (next_mod_time, next_mod_time))
      ...     next_mod_time += 10

    Calling 'cleanup' without a keep arguments will just return without doing
    anything.

      >>> cleanup(backup_dir)

    Cleaning an empty directory won't do a thing.

      >>> cleanup(backup_dir, keep=1)

    Adding one backup file and cleaning the directory won't remove it either:

      >>> add_backup('1.fs')
      >>> cleanup(backup_dir, keep=1)
      >>> ls('back')
      - 1.fs

    Adding a second backup file means the first one gets removed.

      >>> add_backup('2.fs')
      >>> cleanup(backup_dir, keep=1)
      >>> ls('back')
      - 2.fs

    If there are more than one file to remove, the results are OK, too:

      >>> add_backup('3.fs')
      >>> add_backup('4.fs')
      >>> add_backup('5.fs')
      >>> cleanup(backup_dir, keep=1)
      >>> ls('back')
      - 5.fs

    Every other file older than the last full backup that is kept is deleted,
    too. This includes deltas for incremental backups and '.dat' files. Deltas
    and other files added after the last full retained backup are always kept.

      >>> add_backup('5-something.deltafs')
      >>> add_backup('5.dat')
      >>> add_backup('6.fs')
      >>> add_backup('6-something.deltafs')
      >>> cleanup(backup_dir, keep=1)
      >>> ls('back')
      - 6-something.deltafs
      - 6.fs

    Keeping more than one file is also supported.

      >>> add_backup('7.fs')
      >>> add_backup('7-something.deltafs')
      >>> add_backup('7.dat')
      >>> add_backup('8.fs')
      >>> add_backup('8-something.deltafs')
      >>> add_backup('8.dat')
      >>> add_backup('9.fs')
      >>> add_backup('9-something.deltafs')
      >>> add_backup('9.dat')
      >>> cleanup(backup_dir, keep=2)
      >>> ls('back')
      -  8-something.deltafs
      -  8.dat
      -  8.fs
      -  9-something.deltafs
      -  9.dat
      -  9.fs

    """
    if not keep:
        logger.debug("Value of 'keep' is %r, we don't want to remove anything.",
                     keep)
        return
    logger.debug("Trying to clean up old backups.")
    filenames = os.listdir(backup_location)
    logger.debug("Looked up filenames in the target dir: %s found. %r.",
              len(filenames), filenames)
    num_backups = int(keep)
    logger.debug("Max number of backups: %s.", num_backups)
    files_modtimes = []
    for filename in filenames:
        mod_time = os.path.getmtime(os.path.join(backup_location, filename))
        file_ = (filename, mod_time)
        files_modtimes.append(file_)
    # we are only interested in full backups
    fullbackups = [f for f in files_modtimes if f[0].endswith('.fs')]
    logger.debug("Filtered out full backups (*.fs): %r.",
              [f[0] for f in fullbackups])
    if len(fullbackups) > num_backups and num_backups != 0:
        logger.debug("There are older backups that we can remove.")
        fullbackups = sorted(fullbackups, key=itemgetter(1))
        fullbackups.reverse()
        logger.debug("Full backups, sorted by date, newest first: %r.",
                  [f[0] for f in fullbackups])
        oldest_backup_to_keep = fullbackups[(num_backups-1)]
        logger.debug("Oldest backup to keep: %s", oldest_backup_to_keep[0])
        last_date_to_keep = oldest_backup_to_keep[1]
        logger.debug("The oldest backup we get to keep is from %s.",
                  last_date_to_keep)
        for filename, modtime in files_modtimes:
            if modtime < last_date_to_keep:
                filepath = os.path.join(backup_location, filename)
                os.remove(filepath)
                logger.debug("Deleted %s.", filepath)
        logger.info("Removed old backups, the latest %s full backups have "
                 "been kept.", str(num_backups))
    else:
        logger.debug("Not removing backups.")
        if len(fullbackups) <= num_backups:
            logger.debug("Reason: #backups (%s) <= than max (%s).",
                      len(fullbackups), num_backups)
        if num_backups == 0:
            logger.debug("Reason: max # of backups is 0, so that is a "
                      "sign to us to not remove backups.")
