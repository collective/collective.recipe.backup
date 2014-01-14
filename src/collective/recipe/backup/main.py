"""Functions that invoke repozo and/or the blob backup.
"""
import logging
import sys

from collective.recipe.backup import copyblobs
from collective.recipe.backup import repozorunner
from collective.recipe.backup import utils

logger = logging.getLogger('backup')


def backup_main(bin_dir, storages, keep, full,
                verbose, gzip, backup_blobs, only_blobs, use_rsync,
                keep_blob_days=0, pre_command='', post_command='',
                gzip_blob=False, **kwargs):
    """Main method, gets called by generated bin/backup."""
    utils.check_folders(storages, backup_blobs=backup_blobs,
                        only_blobs=only_blobs)
    utils.execute_or_fail(pre_command)
    if not only_blobs:
        result = repozorunner.backup_main(
            bin_dir, storages, keep, full, verbose, gzip)
        if result:
            if backup_blobs:
                logger.error("Halting execution due to error; not backing up "
                             "blobs.")
            else:
                logger.error("Halting execution due to error.")
            sys.exit(1)

    if not backup_blobs:
        utils.execute_or_fail(post_command)
        return
    for storage in storages:
        blobdir = storage['blobdir']
        if not blobdir:
            logger.info("No blob dir defined for %s storage" %
                        storage['storage'])
            continue
        blob_backup_location = storage['blob_backup_location']
        logger.info("Please wait while backing up blobs from %s to %s",
                    blobdir, blob_backup_location)
        copyblobs.backup_blobs(blobdir, blob_backup_location, full,
                               use_rsync, keep=keep,
                               keep_blob_days=keep_blob_days,
                               gzip_blob=gzip_blob)
    utils.execute_or_fail(post_command)


def fullbackup_main(bin_dir, storages, keep, full,
                    verbose, gzip, backup_blobs, only_blobs, use_rsync,
                    keep_blob_days=0, pre_command='',
                    post_command='', gzip_blob=False, **kwargs):
    """Main method, gets called by generated bin/fullbackup."""
    utils.check_folders(storages, backup_blobs=backup_blobs,
                        only_blobs=only_blobs)
    utils.execute_or_fail(pre_command)
    if not only_blobs:
        # Set Full=True for forced full backups.
        # It was easier to do this here, than mess with
        # "script_arguments = arguments_template % opts"
        # in backup.Recipe.install
        full = True
        result = repozorunner.fullbackup_main(
            bin_dir, storages, keep, full, verbose, gzip)
        if result:
            if backup_blobs:
                logger.error("Halting execution due to error; not backing up "
                             "blobs.")
            else:
                logger.error("Halting execution due to error.")
            sys.exit(1)

    if not backup_blobs:
        utils.execute_or_fail(post_command)
        return
    for storage in storages:
        blobdir = storage['blobdir']
        if not blobdir:
            logger.info("No blob dir defined for %s storage" %
                        storage['storage'])
            continue
        blob_backup_location = storage['blob_backup_location']
        logger.info("Please wait while backing up blobs from %s to %s",
                    blobdir, blob_backup_location)
        copyblobs.backup_blobs(blobdir, blob_backup_location, full,
                               use_rsync, keep=keep,
                               keep_blob_days=keep_blob_days,
                               gzip_blob=gzip_blob)
    utils.execute_or_fail(post_command)


def snapshot_main(bin_dir, storages, keep, verbose, gzip,
                  backup_blobs, only_blobs, use_rsync,
                  keep_blob_days=0, pre_command='', post_command='',
                  gzip_blob=False, **kwargs):
    """Main method, gets called by generated bin/snapshotbackup."""
    utils.check_folders(storages, backup_blobs=backup_blobs,
                        only_blobs=only_blobs)
    utils.execute_or_fail(pre_command)
    if not only_blobs:
        result = repozorunner.snapshot_main(
            bin_dir, storages, keep, verbose, gzip)
        if result:
            if backup_blobs:
                logger.error("Halting execution due to error; not backing up "
                             "blobs.")
            else:
                logger.error("Halting execution due to error.")
            sys.exit(1)

    if not backup_blobs:
        utils.execute_or_fail(post_command)
        return
    for storage in storages:
        blobdir = storage['blobdir']
        if not blobdir:
            logger.info("No blob dir defined for %s storage" %
                        storage['storage'])
            continue
        blob_snapshot_location = storage['blob_snapshot_location']
        logger.info("Please wait while making snapshot of blobs from %s to %s",
                    blobdir, blob_snapshot_location)
        copyblobs.backup_blobs(blobdir, blob_snapshot_location,
                               full=True, use_rsync=use_rsync, keep=keep,
                               keep_blob_days=keep_blob_days,
                               gzip_blob=gzip_blob)
    utils.execute_or_fail(post_command)


def restore_main(bin_dir, storages, verbose, backup_blobs,
                 only_blobs, use_rsync, restore_snapshot=False, pre_command='',
                 post_command='', gzip_blob=False, **kwargs):
    """Main method, gets called by generated bin/restore."""
    date = None
    # Try to find a date in the command line arguments
    for arg in sys.argv:
        if arg in ('-q', '-n', '--quiet', '--no-prompt'):
            continue
        if arg.find('restore') != -1:
            continue

        # We can assume this argument is a date
        date = arg
        logger.debug("Argument passed to bin/restore, we assume it is "
                     "a date that we have to pass to repozo: %s.", date)
        logger.info("Date restriction: restoring state at %s." % date)
        break

    question = '\n'
    if not only_blobs:
        question += "This will replace the filestorage:\n"
        for storage in storages:
            question += "    %s\n" % storage.get('datafs')
    if backup_blobs:
        question += "This will replace the blobstorage:\n"
        for storage in storages:
            question += "    %s\n" % storage.get('blobdir')
    question += "Are you sure?"
    if not kwargs.get('no_prompt'):
        if not utils.ask(question, default=False, exact=True):
            logger.info("Not restoring.")
            sys.exit(0)

    utils.execute_or_fail(pre_command)
    if not only_blobs:
        result = repozorunner.restore_main(
            bin_dir, storages, verbose, date,
            restore_snapshot)
        if result:
            if backup_blobs:
                logger.error("Halting execution due to error; not restoring "
                             "blobs.")
            else:
                logger.error("Halting execution due to error.")
            sys.exit(1)

    if not backup_blobs:
        utils.execute_or_fail(post_command)
        return
    for storage in storages:
        blobdir = storage['blobdir']
        if restore_snapshot:
            blob_backup_location = storage['blob_snapshot_location']
        else:
            blob_backup_location = storage['blob_backup_location']
        if not blobdir:
            logger.info("No blob dir defined for %s storage" %
                        storage['storage'])
            continue
        if not blobdir:
            logger.error("No blob storage source specified")
            sys.exit(1)
        logger.info("Restoring blobs from %s to %s", blob_backup_location,
                    blobdir)
        copyblobs.restore_blobs(blob_backup_location, blobdir,
                                use_rsync=use_rsync, date=date,
                                gzip_blob=gzip_blob)
    utils.execute_or_fail(post_command)


def snapshot_restore_main(*args, **kwargs):
    """Main method, gets called by generated bin/snapshotrestore.

    Difference with restore_main is that we get need to use the
    snapshot_location and blob_snapshot_location.
    """
    # Override the locations:
    kwargs['restore_snapshot'] = True
    return restore_main(*args, **kwargs)
