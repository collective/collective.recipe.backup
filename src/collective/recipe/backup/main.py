"""Functions that invoke repozo and/or the blob backup.
"""
from collective.recipe.backup import config
from collective.recipe.backup import copyblobs
from collective.recipe.backup import repozorunner
from collective.recipe.backup import utils

import logging
import sys


logger = logging.getLogger("backup")


def backup_main(
    bin_dir,
    storages,
    keep,
    full,
    verbose,
    gzip,
    backup_blobs,
    only_blobs,
    use_rsync,
    keep_blob_days=0,
    pre_command="",
    post_command="",
    archive_blob=False,
    compress_blob=False,
    rsync_options="",
    quick=True,
    blob_timestamps=False,
    backup_method=config.STANDARD_BACKUP,
    incremental_blobs=False,
    rsync_hard_links_on_first_copy=False,
    **kwargs,
):
    """Main method, gets called by generated bin/backup."""
    if backup_method not in config.BACKUP_METHODS:
        raise RuntimeError(f"Unknown backup method {backup_method}.")
    utils.execute_or_fail(pre_command)
    utils.check_folders(
        storages,
        backup_blobs=backup_blobs,
        only_blobs=only_blobs,
        backup_method=backup_method,
    )
    if not only_blobs:
        result = repozorunner.backup_main(
            bin_dir, storages, keep, full, verbose, gzip, quick, backup_method
        )
        if result:
            if backup_blobs:
                logger.error("Halting execution due to error; not backing up blobs.")
            else:
                logger.error("Halting execution due to error.")
            sys.exit(1)

    if not backup_blobs:
        utils.execute_or_fail(post_command)
        return
    for storage in storages:
        blobdir = storage["blobdir"]
        if not blobdir:
            logger.info("No blob dir defined for %s storage", storage["storage"])
            continue
        blob_backup_location = None
        if backup_method == config.STANDARD_BACKUP:
            blob_backup_location = storage["blob_backup_location"]
            logger.info(
                "Please wait while backing up blobs from %s to %s",
                blobdir,
                blob_backup_location,
            )
        elif backup_method == config.SNAPSHOT_BACKUP:
            blob_backup_location = storage["blob_snapshot_location"]
            logger.info(
                "Please wait while making snapshot of blobs from %s to %s",
                blobdir,
                blob_backup_location,
            )
        elif backup_method == config.ZIP_BACKUP:
            blob_backup_location = storage["blob_zip_location"]
            logger.info(
                "Please wait while backing up blobs from %s to %s",
                blobdir,
                blob_backup_location,
            )
        if only_blobs:
            fs_backup_location = None
        elif backup_method == config.STANDARD_BACKUP:
            fs_backup_location = storage["backup_location"]
        elif backup_method == config.SNAPSHOT_BACKUP:
            fs_backup_location = storage["snapshot_location"]
        elif backup_method == config.ZIP_BACKUP:
            fs_backup_location = storage["zip_location"]
        copyblobs.backup_blobs(
            blobdir,
            blob_backup_location,
            full,
            use_rsync,
            keep=keep,
            keep_blob_days=keep_blob_days,
            archive_blob=archive_blob,
            compress_blob=compress_blob,
            rsync_options=rsync_options,
            timestamps=blob_timestamps,
            fs_backup_location=fs_backup_location,
            incremental_blobs=incremental_blobs,
            rsync_hard_links_on_first_copy=rsync_hard_links_on_first_copy,
        )
    utils.execute_or_fail(post_command)


def snapshot_main(*args, **kwargs):
    """Main method, gets called by generated bin/snapshotbackup."""
    kwargs["full"] = True
    kwargs["incremental_blobs"] = False
    kwargs["backup_method"] = config.SNAPSHOT_BACKUP
    return backup_main(*args, **kwargs)


def zipbackup_main(*args, **kwargs):
    """Main method, gets called by generated bin/zipbackup."""
    kwargs["backup_method"] = config.ZIP_BACKUP
    kwargs["full"] = True
    kwargs["gzip"] = True
    kwargs["archive_blob"] = True
    kwargs["incremental_blobs"] = False
    kwargs["blob_timestamps"] = False
    kwargs["keep"] = 1
    return backup_main(*args, **kwargs)


def check_blobs(
    storages,
    use_rsync,
    restore_snapshot=False,
    archive_blob=False,
    alt_restore=False,
    rsync_options="",
    zip_restore=False,
    blob_timestamps=False,
    date=None,
):
    """Check that blobs can be restored.

    In this check run, we check what the blob backup location is,
    and set this as blob_backup_location, so we have to do this
    only once.
    """
    for storage in storages:
        blobdir = storage["blobdir"]
        if not blobdir:
            logger.info("No blob dir defined for %s storage", storage["storage"])
            continue
        if restore_snapshot:
            blob_backup_location = storage["blob_snapshot_location"]
        elif alt_restore:
            blob_backup_location = storage["blob_alt_location"]
        elif zip_restore:
            blob_backup_location = storage["blob_zip_location"]
        else:
            blob_backup_location = storage["blob_backup_location"]
        if not blob_backup_location:
            logger.error("No blob storage source specified")
            sys.exit(1)
        storage["blob_backup_location"] = blob_backup_location
        result = copyblobs.restore_blobs(
            blob_backup_location,
            blobdir,
            use_rsync=use_rsync,
            date=date,
            archive_blob=archive_blob,
            rsync_options=rsync_options,
            timestamps=blob_timestamps,
            only_check=True,
        )
        if result:
            logger.error("Halting execution: " "restoring blobstorages would fail.")
            sys.exit(1)


def restore_check(
    bin_dir,
    storages,
    verbose,
    backup_blobs,
    only_blobs,
    use_rsync,
    restore_snapshot=False,
    pre_command="",
    post_command="",
    archive_blob=False,
    alt_restore=False,
    rsync_options="",
    quick=True,
    zip_restore=False,
    blob_timestamps=False,
    **kwargs,
):
    """Method to check that a restore will work.

    Returns the chosen date, if any.
    """
    explicit_restore_opts = [restore_snapshot, alt_restore, zip_restore]
    if sum(1 for opt in explicit_restore_opts if opt) > 1:
        logger.error(
            "Must use at most one option of restore_snapshot, "
            "alt_restore and zip_restore."
        )
        sys.exit(1)
    # Try to find a date in the command line arguments
    date = utils.get_date_from_args()

    if not kwargs.get("no_prompt"):
        question = "\n"
        if not only_blobs:
            question += "This will replace the filestorage:\n"
            for storage in storages:
                question += "    {}\n".format(storage.get("datafs"))
        if backup_blobs:
            question += "This will replace the blobstorage:\n"
            for storage in storages:
                if storage.get("blobdir"):
                    question += "    {}\n".format(storage.get("blobdir"))
        question += "Are you sure?"
        if not utils.ask(question, default=False, exact=True):
            logger.info("Not restoring.")
            sys.exit(0)

    utils.execute_or_fail(pre_command)

    # First run some checks.
    if not only_blobs:
        result = repozorunner.restore_main(
            bin_dir,
            storages,
            verbose,
            date,
            restore_snapshot,
            alt_restore,
            zip_restore,
            only_check=True,
        )
        if result:
            logger.error("Halting execution: " "restoring filestorages would fail.")
            sys.exit(1)
    if backup_blobs:
        check_blobs(
            storages,
            use_rsync,
            restore_snapshot=restore_snapshot,
            archive_blob=archive_blob,
            alt_restore=alt_restore,
            rsync_options=rsync_options,
            zip_restore=zip_restore,
            blob_timestamps=blob_timestamps,
            date=date,
        )
    return date


def restore_main(
    bin_dir,
    storages,
    verbose,
    backup_blobs,
    only_blobs,
    use_rsync,
    restore_snapshot=False,
    pre_command="",
    post_command="",
    archive_blob=False,
    alt_restore=False,
    rsync_options="",
    quick=True,
    zip_restore=False,
    blob_timestamps=False,
    incremental_blobs=False,
    **kwargs,
):

    """Main method, gets called by generated bin/restore."""
    # First run several checks, and get the date that should be restored.
    date = restore_check(
        bin_dir,
        storages,
        verbose,
        backup_blobs,
        only_blobs,
        use_rsync,
        restore_snapshot=restore_snapshot,
        pre_command=pre_command,
        post_command=post_command,
        archive_blob=archive_blob,
        alt_restore=alt_restore,
        rsync_options=rsync_options,
        quick=quick,
        zip_restore=zip_restore,
        blob_timestamps=blob_timestamps,
        incremental_blobs=incremental_blobs,
        **kwargs,
    )
    # Checks have passed, now do the real restore.
    if not only_blobs:
        result = repozorunner.restore_main(
            bin_dir, storages, verbose, date, restore_snapshot, alt_restore, zip_restore
        )
        if result:
            if backup_blobs:
                logger.error("Halting execution due to error; not restoring " "blobs.")
            else:
                logger.error("Halting execution due to error.")
            sys.exit(1)

    if not backup_blobs:
        utils.execute_or_fail(post_command)
        return
    for storage in storages:
        blobdir = storage["blobdir"]
        if not blobdir:
            continue
        blob_backup_location = storage["blob_backup_location"]
        logger.info("Restoring blobs from %s to %s", blob_backup_location, blobdir)
        result = copyblobs.restore_blobs(
            blob_backup_location,
            blobdir,
            use_rsync=use_rsync,
            date=date,
            archive_blob=archive_blob,
            rsync_options=rsync_options,
            timestamps=blob_timestamps,
        )
        if result:
            logger.error("Halting execution due to error.")
            sys.exit(1)
    utils.execute_or_fail(post_command)


def snapshot_restore_main(*args, **kwargs):
    """Main method, gets called by generated bin/snapshotrestore.

    Difference with restore_main is that we use the
    snapshot_location and blob_snapshot_location.
    """
    # Override the locations:
    kwargs["restore_snapshot"] = True
    return restore_main(*args, **kwargs)


def alt_restore_main(*args, **kwargs):
    """Main method, gets called by generated bin/altrestore.

    Difference with restore_main is that we use the
    alternative restore sources.
    """
    # Override the locations:
    kwargs["alt_restore"] = True
    return restore_main(*args, **kwargs)


def zip_restore_main(*args, **kwargs):
    """Main method, gets called by generated bin/ziprestore."""
    # Override the locations:
    kwargs["zip_restore"] = True
    # Override another option.
    kwargs["archive_blob"] = True
    return restore_main(*args, **kwargs)
