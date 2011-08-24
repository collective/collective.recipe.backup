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
                blob_storage_source, backup_blobs, only_blobs):
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
    copyblobs.backup_blobs(blob_storage_source, blob_backup_location, full)


def snapshot_main(bin_dir, datafs, snapshot_location, keep, verbose, gzip,
                  additional, blob_snapshot_location, blob_storage_source,
                  backup_blobs, only_blobs):
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
                           full=True)


def restore_main(bin_dir, datafs, backup_location, verbose, additional,
                 blob_backup_location, blob_storage_source, backup_blobs,
                 only_blobs):
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
    copyblobs.restore_blobs(blob_backup_location, blob_storage_source)
