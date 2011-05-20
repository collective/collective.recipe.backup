"""Functions that invoke repozo and/or the blob backup.
"""
import logging
import sys

from collective.recipe.backup import copyblobs
from collective.recipe.backup import repozo

logger = logging.getLogger('backup')


def backup_main(bin_dir, datafs, backup_location, keep, full,
                verbose, gzip, additional, blob_backup_location,
                blob_storage_source, backup_blobs, only_blobs):
    """Main method, gets called by generated bin/backup."""
    if not only_blobs:
        repozo.backup_main(bin_dir, datafs, backup_location, keep, full,
                           verbose, gzip, additional)
    if not backup_blobs:
        return
    if not blob_backup_location:
        logger.error("No blob backup location specified")
        sys.exit(1)
    if not blob_storage_source:
        logger.error("No blob storage source specified")
        sys.exit(1)
    logger.info("Backing up blobs from %s to %s", blob_storage_source,
                blob_backup_location)
    copyblobs.backup_blobs(blob_storage_source, blob_backup_location, full)


def snapshot_main(bin_dir, datafs, snapshot_location, keep, verbose, gzip,
                  additional, blob_snapshot_location, blob_storage_source,
                  backup_blobs, only_blobs):
    """Main method, gets called by generated bin/snapshotbackup."""
    if not only_blobs:
        repozo.snapshot_main(bin_dir, datafs, snapshot_location, keep, verbose,
                             gzip, additional)
    if not backup_blobs:
        return
    if not blob_snapshot_location:
        logger.error("No blob snaphot location specified")
        sys.exit(1)
    if not blob_storage_source:
        logger.error("No blob storage source specified")
        sys.exit(1)
    logger.info("Making snapshot of blobs from %s to %s", blob_storage_source,
                blob_snapshot_location)
    copyblobs.backup_blobs(blob_storage_source, blob_snapshot_location,
                           full=True)


def restore_main(bin_dir, datafs, backup_location, verbose, additional,
                 blob_backup_location, blob_storage_source, backup_blobs,
                 only_blobs):
    """Main method, gets called by generated bin/restore."""

    if not only_blobs:
        repozo.restore_main(bin_dir, datafs, backup_location, verbose,
                            additional)
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
    #copyblobs.restore_blobs(blob_storage_source, blob_backup_location)
    logger.error("Sorry, restoring blobs has not been implemented yet. "
                 "Please copy them yourself.")
    sys.exit(1)
