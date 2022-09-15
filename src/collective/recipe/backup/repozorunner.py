"""Wrapper that invokes repozo.

There are three main methods, these get called by the generated scripts. So
backup_main() for bin/backup, snapshot_main() for bin/snapshotbackup and
restore_main() for bin/restore.

backup_arguments() and restore_arguments() determine the arguments that are to
be passed to bin/repozo.

cleanup() empties old backups from the backup directory to prevent it from
filling up the harddisk.

"""
from collective.recipe.backup import config
from operator import itemgetter

import logging
import os
import sys


logger = logging.getLogger("repozorunner")


def quote_command(command):
    # Quote the program name, so it works even if it contains spaces
    command = " ".join([f'"{x}"' for x in command])
    if sys.platform[:3].lower() == "win":
        # odd, but true: the windows cmd processor can't handle more than
        # one quoted item per string unless you add quotes around the
        # whole line.
        command = f'"{command}"'
    return command


def backup_main(
    bin_dir,
    storages,
    keep,
    full,
    verbose,
    gzip,
    quick,
    backup_method=config.STANDARD_BACKUP,
):
    """Main method, gets called by generated bin/backup."""
    repozo = os.path.join(bin_dir, "repozo")
    if full:
        quick = False

    for storage in storages:
        fs = storage["datafs"]
        if backup_method == config.STANDARD_BACKUP:
            location = storage["backup_location"]
            logger.info(
                "Please wait while backing up database file: %s to %s", fs, location
            )
        elif backup_method == config.SNAPSHOT_BACKUP:
            location = storage["snapshot_location"]
            logger.info(
                "Please wait while making snapshot backup: %s to %s", fs, location
            )
        elif backup_method == config.ZIP_BACKUP:
            location = storage["zip_location"]
            logger.info(
                "Please wait while backing up database file: %s to %s", fs, location
            )
        result = os.system(
            quote_command(
                [repozo]
                + backup_arguments(
                    fs, location, full, verbose, gzip, quick, as_list=True
                )
            )
        )
        logger.debug("Repozo command executed.")
        if result:
            logger.error("Repozo command failed. See message above.")
            return result
        cleanup(location, keep)


def restore_main(
    bin_dir,
    storages,
    verbose,
    date=None,
    restore_snapshot=False,
    alt_restore=False,
    zip_restore=False,
    only_check=False,
):
    """Main method, gets called by generated bin/restore.

    If only_check is True, we only perform checks.
    Most importantly: check if the backup exists.
    It is not meant as a dry run: we might create a missing directory,
    which serves as a check that the user is allowed to do this.

    The idea is to first call this with only_check=True, and do the same for
    restore_blobs.  When all is well, call it normally without only_check.
    """
    explicit_restore_opts = [restore_snapshot, alt_restore, zip_restore]
    if sum(1 for opt in explicit_restore_opts if opt) > 1:
        logger.error(
            "Must use at most one option of restore_snapshot, "
            "alt_restore and zip_restore."
        )
        sys.exit(1)
    repozo = os.path.join(bin_dir, "repozo")
    logger.debug("If things break: did you stop zope?")
    for storage in storages:
        if restore_snapshot:
            backup_location = storage["snapshot_location"]
        elif alt_restore:
            backup_location = storage["alt_location"]
        elif zip_restore:
            backup_location = storage["zip_location"]
        else:
            backup_location = storage["backup_location"]
        fs = storage["datafs"].rstrip(os.sep)
        fs_dir = os.path.dirname(fs)
        if not os.path.exists(fs_dir):
            os.makedirs(fs_dir)
            logger.info("Created directory %s", fs_dir)
        arguments = restore_arguments(fs, backup_location, date, verbose, as_list=True)
        if only_check:
            continue
        logger.info(
            "Please wait while restoring database file: %s to %s", backup_location, fs
        )
        result = os.system(quote_command([repozo] + arguments))
        if result:
            logger.error("Repozo command failed. See message above.")
            return result


def backup_arguments(
    datafs=None,
    backup_location=None,
    full=False,
    verbose=False,
    gzip=False,
    quick=False,
    as_list=False,
):
    """
    >>> backup_arguments()
    Traceback (most recent call last):
    ...
    RuntimeError: Missing locations.
    >>> backup_arguments(datafs='in/Data.fs', backup_location='out')
    '--backup -f in/Data.fs -r out'
    >>> backup_arguments(datafs='in/Data.fs', backup_location='out',
    ...                  full=True)
    '--backup -f in/Data.fs -r out -F'
    >>> backup_arguments(datafs='in/Data.fs', backup_location='out',
    ...                  quick=True)
    '--backup -f in/Data.fs -r out --quick'

    """
    if datafs is None or backup_location is None:
        raise RuntimeError("Missing locations.")
    arguments = []
    arguments.append("--backup")
    arguments.append("-f")
    arguments.append(datafs)
    arguments.append("-r")
    arguments.append(backup_location)
    if quick:
        # From the repozo help text:
        # Verify via md5 checksum only the last incremental written.
        # This significantly reduces the disk i/o at the (theoretical)
        # cost of inconsistency.  This is a probabilistic way of
        # determining whether a full backup is necessary.
        arguments.append("--quick")
    if full:
        # By default, there's an incremental backup, if possible.
        arguments.append("-F")
    else:
        logger.debug(
            "You are not making a full backup. Note that if there "
            "are no changes since the last backup, there will not "
            "be a new incremental backup file."
        )
    if verbose:
        arguments.append("--verbose")
    if gzip:
        arguments.append("--gzip")

    logger.debug("Repozo arguments used: %s", " ".join(arguments))
    if as_list:
        return arguments
    return " ".join(arguments)


def restore_arguments(
    datafs=None, backup_location=None, date=None, verbose=False, as_list=False
):
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
    arguments.append("--recover")
    arguments.append("-o")
    arguments.append(datafs)
    arguments.append("-r")
    arguments.append(backup_location)

    if date is not None:
        logger.debug("Restore as of date %r requested.", date)
        arguments.append("-D")
        arguments.append(date)
    if verbose:
        arguments.append("--verbose")
    logger.debug("Repozo arguments used: %s", " ".join(arguments))
    if as_list:
        return arguments
    return " ".join(arguments)


def cleanup(backup_location, keep=0):
    """Clean up old backups

    For the test, we create a backup dir using buildout's test support methods:

      >>> backup_dir = 'back'
      >>> mkdir(backup_dir)

    And we'll make a function that creates a backup file for us and that also
    sets the file modification dates to a meaningful time.

      >>> import time
      >>> import os
      >>> next_mod_time = time.time() - 1000
      >>> def add_backup(name):
      ...     global next_mod_time
      ...     write(backup_dir, name, 'dummycontents')
      ...     # Change modification time, every new file is 10 seconds older.
      ...     os.utime(join(backup_dir, name), (next_mod_time, next_mod_time))
      ...     next_mod_time += 10

    Calling 'cleanup' without a keep arguments will just return without doing
    anything.

      >>> cleanup(backup_dir)

    Cleaning an empty directory won't do a thing.

      >>> cleanup(backup_dir, keep=1)

    Adding one backup file and cleaning the directory won't remove it either:

      >>> add_backup('1.fs')
      >>> cleanup(backup_dir, keep=1)
      >>> ls(backup_dir)
      - 1.fs

    Adding a second backup file means the first one gets removed.

      >>> add_backup('2.fs')
      >>> cleanup(backup_dir, keep=1)
      >>> ls(backup_dir)
      - 2.fs

    If there are more than one file to remove, the results are OK, too:

      >>> add_backup('3.fs')
      >>> add_backup('4.fs')
      >>> add_backup('5.fs')
      >>> cleanup(backup_dir, keep=1)
      >>> ls(backup_dir)
      - 5.fs

    Every other file older than the last full backup that is kept is deleted,
    too. This includes deltas for incremental backups and '.dat' files. Deltas
    and other files added after the last full retained backup are always kept.

      >>> add_backup('5-something.deltafs')
      >>> add_backup('5.dat')
      >>> add_backup('6.fs')
      >>> add_backup('6-something.deltafs')
      >>> cleanup(backup_dir, keep=1)
      >>> ls(backup_dir)
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
      >>> ls(backup_dir)
      -  8-something.deltafs
      -  8.dat
      -  8.fs
      -  9-something.deltafs
      -  9.dat
      -  9.fs

    Keep = 0 doesn't delete anything.

      >>> cleanup(backup_dir, keep=0)
      >>> ls(backup_dir)
      -  8-something.deltafs
      -  8.dat
      -  8.fs
      -  9-something.deltafs
      -  9.dat
      -  9.fs

    Back to keep=2, we test that .fsz files (made with repozo's ``--gzip``
    option) are also treated as full backups.

      >>> add_backup('10.fsz')
      >>> cleanup(backup_dir, keep=2)
      >>> ls(backup_dir)
      -  10.fsz
      -  9-something.deltafs
      -  9.dat
      -  9.fs

      >>> remove(backup_dir)

    """
    keep = int(keep)  # Making sure.
    if not keep:
        logger.debug("Value of 'keep' is %r, we don't want to remove anything.", keep)
        return
    logger.debug("Trying to clean up old backups.")
    filenames = sorted(os.listdir(backup_location))
    logger.debug(
        "Looked up filenames in the target dir: %s found. %r.",
        len(filenames),
        filenames,
    )
    num_backups = int(keep)
    logger.debug("Max number of backups: %s.", num_backups)
    files_modtimes = []
    for filename in filenames:
        mod_time = os.path.getmtime(os.path.join(backup_location, filename))
        file_ = (filename, mod_time)
        files_modtimes.append(file_)
    # we are only interested in full backups
    fullbackups = [
        f for f in files_modtimes if f[0].endswith(".fs") or f[0].endswith(".fsz")
    ]
    logger.debug(
        "Filtered out full backups (*.fs/*.fsz): %r.", [f[0] for f in fullbackups]
    )
    fullbackups = sorted(fullbackups, key=itemgetter(1))
    logger.debug("%d fullbackups: %r", len(fullbackups), fullbackups)
    if len(fullbackups) > num_backups and num_backups != 0:
        logger.debug("There are older backups that we can remove.")
        fullbackups.reverse()
        logger.debug(
            "Full backups, sorted by date, newest first: %r.",
            [f[0] for f in fullbackups],
        )
        oldest_backup_to_keep = fullbackups[(num_backups - 1)]
        logger.debug("Oldest backup to keep: %s", oldest_backup_to_keep[0])
        last_date_to_keep = oldest_backup_to_keep[1]
        logger.debug("The oldest backup we get to keep is from %s.", last_date_to_keep)
        deleted = 0
        # Note: this also deletes now outdated .deltafs and .dat
        # files, so we may easily delete more items than there are
        # fullbackups (so num_backups + deleted may be more than
        # len(fullbackups).
        for filename, modtime in files_modtimes:
            if modtime < last_date_to_keep:
                filepath = os.path.join(backup_location, filename)
                os.remove(filepath)
                logger.debug("Deleted %s.", filepath)
                deleted += 1
        logger.info(
            "Removed %d file(s) belonging to old backups, the latest "
            "%s full backups have been kept.",
            deleted,
            str(num_backups),
        )
        if deleted == 0:
            # This may be a programming/testing error.
            logger.error("We should have deleted something, but didn't...")
    else:
        logger.debug("Not removing backups.")
        if len(fullbackups) <= num_backups:
            logger.debug(
                "Reason: #backups (%s) <= than max (%s).", len(fullbackups), num_backups
            )
        if num_backups == 0:
            logger.debug(
                "Reason: max # of backups is 0, so that is a "
                "sign to us to not remove backups."
            )
