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
                blob_storage_source, backup_blobs, only_blobs, use_rsync):
    """Main method, gets called by generated bin/backup."""
    if not only_blobs:
        repozorunner.backup_main(
            bin_dir, datafs, backup_location, keep, full, verbose, gzip,
            additional)
    if not backup_blobs:
        return
    if not blob_backup_location:
        logger.error("No blob backup location specified")
        sys.exit(1)
    if not blob_storage_source:
        logger.error("No blob storage source specified")
        sys.exit(1)
    logger.info("Please wait while backing up blobs from %s to %s",
                blob_storage_source, blob_backup_location)
    if not full:
        # Removing old blob backups only makes sense for full backups,
        # as there is no direct translation from a backup of a Data.fs
        # plus its incremental backups to a list of blob backups.
        #
        # TODO: maybe specifically allow blob_keep=5d/2w/1m (5 days, 2
        # weeks, 1 month)
        keep = 0
    copyblobs.backup_blobs(blob_storage_source, blob_backup_location, full,
                           use_rsync, keep=keep)


def snapshot_main(bin_dir, datafs, snapshot_location, keep, verbose, gzip,
                  additional, blob_snapshot_location, blob_storage_source,
                  backup_blobs, only_blobs, use_rsync):
    """Main method, gets called by generated bin/snapshotbackup."""
    if not only_blobs:
        repozorunner.snapshot_main(
            bin_dir, datafs, snapshot_location, keep, verbose, gzip,
            additional)
    if not backup_blobs:
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
                           full=True, use_rsync=use_rsync, keep=keep)


def restore_main(bin_dir, datafs, backup_location, verbose, additional,
                 blob_backup_location, blob_storage_source, backup_blobs,
                 only_blobs, use_rsync):
    """Main method, gets called by generated bin/restore."""
    question = '\n'
    if not only_blobs:
        question += "This will replace the filestorage (Data.fs).\n"
    if backup_blobs:
        question += "This will replace the blobstorage.\n"
    question += "Are you sure?"
    if not utils.ask(question, default=False, exact=True):
        logger.info("Not restoring.")
        sys.exit(0)

    if not only_blobs:
        repozorunner.restore_main(
            bin_dir, datafs, backup_location, verbose, additional)
    if not backup_blobs:
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
                            use_rsync)
