# Wrapper that invokes repozo.
from operator import itemgetter
import os
import logging

logger = logging.getLogger('backup')


def main(bin_dir, datafs, backup_location, keep):
    """Main method, gets called by generated bin/backup."""
    repozo = os.path.join(bin_dir, 'repozo')
    logger.info("Backing up database file: %s to %s...",
                datafs, backup_location)
    os.system(repozo + ' ' +
              backup_arguments(datafs, backup_location, keep))


def backup_arguments(datafs=None,
                     backup_location=None,
                     keep=None,
                     #full=False,
                     ):
    """
      >>> 3 + 4
      7
    """
    arguments = []
    arguments.append('--backup')
    arguments.append('-f %s' % datafs)
    arguments.append('-r %s' % backup_location)
    #if full:
    #    arguments.append('--full')
    #    # By default, there's an incremental backup, if possible.
    args = ' '.join(arguments)
    logger.info("Command used: %s", args)
    return args


def cleanup():
    # We want to clean up old backups automaticly.
    # The number_of_backups var tells us how many full backups we want
    # to keep.
    logger.debug("Trying to clean up old backups.")
    filenames = os.listdir(backup_location)
    logger.debug("Looked up filenames in the target dir: %s found. %r.",
              len(filenames), filenames)
    num_backups = conf.numberOfBackups()
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
