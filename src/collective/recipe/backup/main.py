"""Functions that invoke repozo and/or the blob backup.
"""
import logging
import sys

from collective.recipe.backup import copyblobs
from collective.recipe.backup import repozorunner
from collective.recipe.backup import utils

logger = logging.getLogger('backup')


def backup_main(bin_dir, datafs, backup_location, keep, full,
                verbose, gzip, additional, blob_backup_location,
                blob_storage_source, backup_blobs, only_blobs, use_rsync,
                keep_blob_days=0, pre_command='', post_command='', **kwargs):
    """Main method, gets called by generated bin/backup."""
    utils.execute_or_fail(pre_command)
    if not only_blobs:
        result = repozorunner.backup_main(
            bin_dir, datafs, backup_location, keep, full, verbose, gzip,
            additional)
        if result and backup_blobs:
            logger.error("Halting execution due to error; not backing up "
                         "blobs.")

    if not backup_blobs:
        utils.execute_or_fail(post_command)
        return
    if not blob_backup_location:
        logger.error("No blob backup location specified")
        sys.exit(1)
    if not blob_storage_source:
        logger.error("No blob storage source specified")
        sys.exit(1)
    logger.info("Please wait while backing up blobs from %s to %s",
                blob_storage_source, blob_backup_location)
    copyblobs.backup_blobs(blob_storage_source, blob_backup_location, full,
                           use_rsync, keep=keep, keep_blob_days=keep_blob_days)
    utils.execute_or_fail(post_command)


def snapshot_main(bin_dir, datafs, snapshot_location, keep, verbose, gzip,
                  additional, blob_snapshot_location, blob_storage_source,
                  backup_blobs, only_blobs, use_rsync, keep_blob_days=0,
                  pre_command='', post_command='', **kwargs):
    """Main method, gets called by generated bin/snapshotbackup."""
    utils.execute_or_fail(pre_command)
    if not only_blobs:
        result = repozorunner.snapshot_main(
            bin_dir, datafs, snapshot_location, keep, verbose, gzip,
            additional)
        if result and backup_blobs:
            logger.error("Halting execution due to error; not backing up "
                         "blobs.")
    if not backup_blobs:
        utils.execute_or_fail(post_command)
        return
    if not blob_snapshot_location:
        logger.error("No blob snaphot location specified")
        sys.exit(1)
    if not blob_storage_source:
        logger.error("No blob storage source specified")
        sys.exit(1)
    logger.info("Please wait while making snapshot of blobs from %s to %s",
                blob_storage_source, blob_snapshot_location)
    copyblobs.backup_blobs(blob_storage_source, blob_snapshot_location,
                           full=True, use_rsync=use_rsync, keep=keep,
                           keep_blob_days=keep_blob_days)
    utils.execute_or_fail(post_command)


def restore_main(bin_dir, datafs, backup_location, verbose, additional,
                 blob_backup_location, blob_storage_source, backup_blobs,
                 only_blobs, use_rsync, pre_command='', post_command='',
                 **kwargs):
    """Main method, gets called by generated bin/restore."""
    date = None
    if len(sys.argv) > 1:
        date = sys.argv[1]
        logger.debug("Argument passed to bin/restore, we assume it is "
                     "a date that we have to pass to repozo: %s.", date)
        logger.info("Date restriction: restoring state at %s." % date)

    question = '\n'
    if not only_blobs:
        question += "This will replace the filestorage (Data.fs).\n"
    if backup_blobs:
        question += "This will replace the blobstorage.\n"
    question += "Are you sure?"
    if not utils.ask(question, default=False, exact=True):
        logger.info("Not restoring.")
        sys.exit(0)

    utils.execute_or_fail(pre_command)
    if not only_blobs:
        result = repozorunner.restore_main(
            bin_dir, datafs, backup_location, verbose, additional, date)
        if result and backup_blobs:
            logger.error("Halting execution due to error; not restoring "
                         "blobs.")
            sys.exit(1)

    if not backup_blobs:
        utils.execute_or_fail(post_command)
        return
    if not blob_backup_location:
        logger.error("No blob backup location specified")
        sys.exit(1)
    if not blob_storage_source:
        logger.error("No blob storage source specified")
        sys.exit(1)
    logger.info("Restoring blobs from %s to %s", blob_backup_location,
                blob_storage_source)
    copyblobs.restore_blobs(blob_backup_location, blob_storage_source,
                            use_rsync=use_rsync, date=date)
    utils.execute_or_fail(post_command)


def snapshot_restore_main(*args, **kwargs):
    """Main method, gets called by generated bin/snapshotrestore.

    Difference with restore_main is that we get need to use the
    snapshot_location and blob_snapshot_location.
    """
    # Override the locations:
    kwargs['backup_location'] = kwargs['snapshot_location']
    kwargs['blob_backup_location'] = kwargs['blob_snapshot_location']
    return restore_main(*args, **kwargs)
