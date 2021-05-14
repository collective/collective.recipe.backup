"""
The idea is to use rsync and hard links; this probably requires a
unixy (Linux, Mac OS X) operating system.

It is based on this article by Mike Rubel:
http://www.mikerubel.org/computers/rsync_snapshots/
"""

from collective.recipe.backup import utils
from datetime import datetime

import logging
import os
import re
import shutil
import sys
import time


logger = logging.getLogger("blobs")
SOURCE = "blobstorage"
BACKUP_DIR = "backups"
# Similar to is_data_file in repozo.py:
is_time_stamp = re.compile(r"\d{4}(?:-\d\d){5}$").match


def find_suffixes(value, suffixes):
    """Check that value contains ons of the suffixes.

    If it does, return the value without suffix.
    It it does not, return None.
    """
    if isinstance(suffixes, utils.stringtypes):
        suffixes = [suffixes]
    # Order the suffixes from large to small.
    # Otherwise looking for 'tar' will find 'delta.tar' too,
    # which will trip up our logic.
    suffixes = sorted(suffixes, key=len, reverse=True)
    found = False
    for suffix in suffixes:
        if not suffix.startswith("."):
            suffix = "." + suffix
        if value.endswith(suffix):
            found = True
            break
    if not found:
        return
    value = value[: -len(suffix)]
    return value


def get_prefix_and_number(value, prefix=None, suffixes=None):
    """Get prefix and number out of value.

    The number we search for is an integer or a timestamp.

    suffixes may be one suffix, or a list of possible suffixes.

    value must start with prefix and end with suffix.
    It must be prefix.number.suffix

    If prefix is None, we don't care what the value starts with.
    If it is an empty string, there must be nothing in front of the number.

    For suffix it must be an explicit suffix or nothing.

    We return None or a string containing the number.

    This can probably be done with one regular expression,
    but it would be hard to read.
    """
    if suffixes is not None:
        value = find_suffixes(value, suffixes)
        if value is None:
            return
    if prefix is None:
        # number or anything.number.
        # But 'anything' should not contain dots: too tricky.
        dots = value.count(".")
        if dots > 1:
            return
        if dots == 1:
            prefix, value = value.split(".")
        else:
            prefix = ""
    else:
        # A dot at the end would be a coding error.
        if not prefix.endswith("."):
            prefix += "."
        if not value.startswith(prefix):
            return
        value = value[len(prefix) :]
    # At this point, we really should only have a number left.
    try:
        int(value)
    except ValueError:
        if not is_time_stamp(value):
            return
    if prefix:
        # return prefix without dot
        prefix = prefix.rstrip(".")
    return prefix, value


def number_key(value):
    """Key for comparing backup numbers, sorting oldest first.

    The value MUST be a string with either an integer or a timestamp.
    So '0', '1', '2', '10 '1999-12-31-23-59-30'.

    We return a tuple (x, y).
    x indicates a number (0) or timestamp (1).
    y is the negative of the integer or the original string.

    This makes sure that the largest integer is sorted first,
    and the newest timestamp is sorted last.
    This used to be the other way around, but had to be changed
    in order to use comparison by key, which is the only comparison
    supported in Python 3.

    Sample input may be '0', '1', '2', '10', '2000-12-31-23-59-30',
    '1999-12-31-23-59-30'.
    """
    try:
        # make number negative
        value = -int(value)
        type_indicator = 0
    except ValueError:
        if not is_time_stamp(value):
            raise ValueError(f"No integer and no timestamp in {value}.")
        # timestamp
        type_indicator = 1
    return (type_indicator, value)


def first_number_key(value):
    """Key for comparing backup numbers.

    value MUST be (number, modification_time, ...).
    We are primarily interested in the number.
    But if that is the same, we look at the modification time.
    """
    return number_key(value[0]), value[1]


def mod_time_number_key(value):
    """Key for comparing backups.

    value MUST be (number, modification_time, ...).
    We are primarily interested in the modification time.
    But in tests this may not be unique enough,
    as lots of backups are made quickly after each other,
    so use the number key as extra.
    """
    return value[1], number_key(value[0])


def part_of_same_backup(values):
    """Validate that values belong to the same backup.

    values MUST be something like blobstorage.0 or
    blobstorage.1999-12-31-23-59-30.
    """
    if not values:
        return True
    first = values[0]
    if "." not in first:
        raise ValueError(f"Expected '.' in backup name {first}")
    start = first.rsplit(".", 1)[0]
    for value in values:
        start2 = value.rsplit(".", 1)[0]
        if start != start2:
            raise ValueError(f"Not the same start for backups: {first} vs {value}")


def part_of_same_archive_backup(values):
    """Validate that values belong to the same archive backup.

    values MUST be something like blobstorage.0.tar.gz or
    blobstorage.1999-12-31-23-59-30.tar.
    """
    if not values:
        return True
    suffixes = [".tar", ".tar.gz"]
    cleaned = []
    for candidate in values:
        correct = False
        for suffix in suffixes:
            if candidate.endswith(suffix):
                correct = True
                cleaned.append(candidate[: -len(suffix)])
                break
        if not correct:
            raise ValueError(f"{candidate} does not end with {suffix}")
    return part_of_same_backup(cleaned)


def backup_key(value):
    """Key for comparing backups.

    You should call part_of_same_backup on values,
    so we can assume that value is something like blobstorage.0 or
    blobstorage.1999-12-31-23-59-30.
    """
    num = value.rsplit(".", 1)[-1]
    return number_key(num)


def archive_backup_key(value):
    """Key for comparing backup archives.

    You should call part_of_same_backup on values,
    so we can assume that value is something like blobstorage.0.tar.gz or
    blobstorage.1999-12-31-23-59-30.tar.
    """
    suffixes = [".tar", ".tar.gz"]
    for suffix in suffixes:
        if value.endswith(suffix):
            value = value[: -len(suffix)]
            break
    return backup_key(value)


def gen_timestamp(now=None):
    """Generate timestamp.

    With 'now' you can set a different time for testing.
    It should be a tuple of year, month, day, hour, minute, second.
    A number (like time.time()) works too.
    """
    if now is None or isinstance(now, (int, float)):
        now = time.gmtime(now)[:6]
    return "{:04d}-{:02d}-{:02d}-{:02d}-{:02d}-{:02d}".format(*now)


def get_valid_directories(container, name):
    """Get subdirectories in container that start with 'name'.

    Subdirectories are expected to be something like blobstorage.0,
    blobstorage.1, etc.  We refuse to work when an accepted name is
    not actually a directory as this will mess up our logic further
    on.  No one should manually add files or directories here.

    Note: timestamps are not accepted here.  This function is not used
    in scenarios that use timestamps.

    Using the zc.buildout tools we create some directories and files:

    >>> mkdir('dirtest')
    >>> get_valid_directories('dirtest', 'a')
    []
    >>> for d in ['a', 'a.0', 'a.1', 'a.bar.2', 'a.bar',
    ...         'a.2017-01-02-03-04-05']:
    ...     mkdir('dirtest', d)
    >>> sorted(get_valid_directories('dirtest', 'a'))
    ['a.0', 'a.1']
    >>> get_valid_directories('dirtest', 'bar')
    []

    We break when encountering a correct name that is a file where we
    expect a directory, as this will break the rotating functionality.

    >>> write('dirtest', 'a.3', 'Test file.')
    >>> get_valid_directories('dirtest', 'a')
    Traceback (most recent call last):
    ...
    Exception: Refusing to rotate a.3 as it is not a directory.
    >>> get_valid_directories('dirtest', 'bar')
    []

    Cleanup:

    >>> remove('dirtest')

    """
    valid_entries = []
    for entry in sorted(os.listdir(container)):
        if not entry.startswith(name + "."):
            continue
        entry_start, entry_num = entry.rsplit(".", 1)
        if entry_start != name:
            # Maybe something like 'blobstorage.break.me.0'
            logger.warning("Ignoring entry %s in %s", entry, container)
            continue
        try:
            entry_num = int(entry_num)
        except (ValueError, TypeError):
            continue
        # Looks like we have a winner.  It must be a directory though.
        if not os.path.isdir(os.path.join(container, entry)):
            raise Exception(f"Refusing to rotate {entry} as it is not a directory.")
        valid_entries.append(entry)
    return valid_entries


def get_valid_archives(container, name):
    """Get gzip files in container that start with 'name'.

    Gzip files are expected to be something like blobstorage.0.tar,
    blobstorage.1.tar.gz, etc.  We refuse to work when an accepted name is
    not actually a file as this will mess up our logic further
    on.  No one should manually add files or directories here.

    Both tar and tar.gz are accepted.

    Note: timestamps are not accepted here.  This function is not used
    in scenarios that use timestamps.

    Using the zc.buildout tools we create some directories and files:

    >>> mkdir('dirtest')
    >>> get_valid_archives('dirtest', 'a.tar.gz')
    []
    >>> for gz in ['a.tar.gz', 'a.0.tar.gz', 'a.1.tar', 'a.bar.2.tar.gz',
    ...         'a.2017-01-02-03-04-05.tar.gz']:
    ...     write('dirtest', gz, 'Test file.')
    >>> sorted(get_valid_archives('dirtest', 'a'))
    ['a.0.tar.gz', 'a.1.tar']
    >>> get_valid_archives('dirtest', 'bar')
    []

    We break when encountering a correct name that is a directory where we
    expect a file.

    >>> mkdir('dirtest', 'a.3.tar')
    >>> get_valid_archives('dirtest', 'a')
    Traceback (most recent call last):
    ...
    Exception: Refusing to rotate a.3.tar as it is not a file.
    >>> get_valid_archives('dirtest', 'bar')
    []

    Cleanup:

    >>> remove('dirtest')
    """
    valid_entries = []
    for entry in sorted(os.listdir(container)):
        matched = re.match(rf"^{name}\.(\d+)\.tar(\.gz)?$", entry)
        if matched is None:
            continue
        match = matched.groups()[0]
        try:
            int(match)
        except (ValueError, TypeError):
            continue
        if not os.path.isfile(os.path.join(container, entry)):
            raise Exception(f"Refusing to rotate {entry} as it is not a file.")
        valid_entries.append(entry)
    return valid_entries


def rotate_directories(container, name):
    """Rotate subdirectories in container that start with 'name'.

    Note: timestamps are not handled here.  This function is not used
    in scenarios that use timestamps.

    Using the zc.buildout tools we create some directories and files:

    >>> mkdir('dirtest')
    >>> rotate_directories('dirtest', 'a')
    >>> for d in ['a.0', 'a.1', 'a.2', 'a.9']:
    ...     mkdir('dirtest', d)
    >>> ls('dirtest')
    d  a.0
    d  a.1
    d  a.2
    d  a.9
    >>> rotate_directories('dirtest', 'a')
    >>> ls('dirtest')
    d  a.1
    d  a.10
    d  a.2
    d  a.3
    >>> rotate_directories('dirtest', 'a')
    >>> ls('dirtest')
    d  a.11
    d  a.2
    d  a.3
    d  a.4

    Cleanup:

    >>> remove('dirtest')

    """
    previous_backups = get_valid_directories(container, name)
    sorted_backups = sorted(previous_backups, key=backup_key)
    # Rotate the directories.
    for directory in sorted_backups:
        new_num = int(directory.split(".")[-1]) + 1
        new_name = f"{name}.{new_num}"
        logger.info("Renaming %s to %s.", directory, new_name)
        os.rename(os.path.join(container, directory), os.path.join(container, new_name))


def rotate_archives(container, name):
    """Rotate archive files in container that start with 'name'.

    Both tar and tar.gz are accepted.

    Note: timestamps are not handled here.  This function is not used
    in scenarios that use timestamps.

    Using the zc.buildout tools we create some directories and files:

    >>> mkdir('dirtest')
    >>> rotate_archives('dirtest', 'a')
    >>> for gz in ['a.0.tar', 'a.1.tar.gz', 'a.2.tar', 'a.9.tar.gz']:
    ...     write('dirtest', gz, 'File content.')
    >>> ls('dirtest')
    -  a.0.tar
    -  a.1.tar.gz
    -  a.2.tar
    -  a.9.tar.gz
    >>> rotate_archives('dirtest', 'a')
    >>> ls('dirtest')
    -  a.1.tar
    -  a.10.tar.gz
    -  a.2.tar.gz
    -  a.3.tar
    >>> rotate_archives('dirtest', 'a')
    >>> ls('dirtest')
    -  a.11.tar.gz
    -  a.2.tar
    -  a.3.tar.gz
    -  a.4.tar

    Cleanup:

    >>> remove('dirtest')

    """
    previous_backups = get_valid_archives(container, name)
    sorted_backups = sorted(previous_backups, key=archive_backup_key)
    # Rotate the directories.
    for entry in sorted_backups:
        matched = re.match(rf"^{name}\.(\d+)\.tar(\.gz)?$", entry)
        old_num, gz = matched.groups()
        new_num = int(old_num) + 1
        if gz is None:
            gz = ""
        new_name = f"{name}.{new_num}.tar{gz}"
        logger.info("Renaming %s to %s.", entry, new_name)
        os.rename(os.path.join(container, entry), os.path.join(container, new_name))


def get_blob_backup_dirs(backup_location, only_timestamps=False):
    """Get blob backup dirs from this location.

    If only_timestamps is True, we only return backups that have timestamps.
    That is useful when restoring.
    """
    filenames = sorted(os.listdir(backup_location))
    logger.debug(
        "Looked up filenames in the target dir: %s found. %r.",
        len(filenames),
        filenames,
    )
    backup_dirs = []
    prefix = ""
    for filename in filenames:
        # We only want directories of the form prefix.X, where X is an
        # integer or a timestamp.  There should not be anything else,
        # but we like to be safe.
        full_path = os.path.join(backup_location, filename)
        if not os.path.isdir(full_path):
            continue
        if filename in (os.curdir, os.pardir):
            # These should not be listed by os.listdir, but again: we
            # like to be safe.
            continue
        parts = get_prefix_and_number(filename)
        if parts is None:
            continue
        num = parts[1]
        if only_timestamps and not is_time_stamp(num):
            continue
        if prefix:
            if parts[0] != prefix:
                logger.error(
                    "Different backup prefixes found in %s (%s, %s). Are you "
                    "mixing two backups in one directory? For safety we will "
                    "exit, because we cannot get a correct sort order.",
                    backup_location,
                    prefix,
                    parts[0],
                )
                sys.exit(1)
        else:
            prefix = parts[0]
        mod_time = os.path.getmtime(full_path)
        backup_dirs.append((num, mod_time, full_path))
    # We always sort by backup number:
    backup_dirs = sorted(backup_dirs, key=first_number_key, reverse=True)
    # Check if this is the same as reverse sorting by modification time:
    mod_times = sorted(backup_dirs, key=mod_time_number_key, reverse=True)
    if backup_dirs != mod_times:
        logger.warning(
            "Sorting blob backups by number gives other result than "
            "reverse sorting by last modification time. "
            "By number: %r. By mod time: %r",
            backup_dirs,
            mod_times,
        )
    logger.debug(
        "Found %d blob backups: %r.", len(backup_dirs), [d[1] for d in backup_dirs]
    )
    return backup_dirs


def get_blob_backup_archives(
    backup_location, only_timestamps=False, include_snapshot_files=False
):
    """Get blob backup archive files from this location.

    Archives may be .tar or .tar.gz files.
    Or delta.tar or delta.tar.gz files.
    If include_snapshot_files is true, it can be .snar files.
    We return all.

    If only_timestamps is True, we only return backups that have timestamps.
    That is useful when restoring.
    """
    filenames = sorted(os.listdir(backup_location))
    logger.debug(
        "Looked up filenames in the target dir: %s found. %r.",
        len(filenames),
        filenames,
    )
    backup_archives = []
    suffixes = ["delta.tar.gz", "delta.tar", "tar.gz", "tar"]
    if include_snapshot_files:
        suffixes += ["snar"]
    prefix = ""
    for filename in filenames:
        # We only want files of the form prefix.X.tar.gz, where X is an
        # integer or a timestamp.  There should not be anything else,
        # but we like to be safe.
        # For the deltas, there can be only timestamps, so we might optimize.
        full_path = os.path.join(backup_location, filename)
        if not os.path.isfile(full_path):
            continue
        parts = get_prefix_and_number(filename, suffixes=suffixes)
        if parts is None:
            continue
        num = parts[1]
        if only_timestamps and not is_time_stamp(num):
            continue
        if prefix:
            if parts[0] != prefix:
                logger.error(
                    "Different backup prefixes found in %s (%s, %s). Are you "
                    "mixing two backups in one directory? For safety we will "
                    "exit, because we cannot get a correct sort order.",
                    backup_location,
                    prefix,
                    parts[0],
                )
                sys.exit(1)
        else:
            prefix = parts[0]

        mod_time = os.path.getmtime(full_path)
        backup_archives.append((num, mod_time, full_path))

    # We always sort by backup number:
    backup_archives = sorted(backup_archives, key=first_number_key, reverse=True)
    # Check if this is the same as reverse sorting by modification time.
    # This might indicate a problem.  We must ignore snapshot files here,
    # because they have the timestamp of the full tar they belong too,
    # and the modification time of the latest delta.
    if include_snapshot_files:
        tars = [x for x in backup_archives if not is_snar(x[2])]
    else:
        tars = list(backup_archives)  # makes a copy
    mod_times = sorted(tars, key=mod_time_number_key, reverse=True)
    if tars != mod_times:
        logger.warning(
            "Sorting blob archive backups by number gives other result than "
            "reverse sorting by last modification time. "
            "By number: %r. By mod time: %r",
            tars,
            mod_times,
        )
    logger.debug(
        "Found %d blob backups: %r.",
        len(backup_archives),
        [d[1] for d in backup_archives],
    )
    return backup_archives


def get_blob_backup_all_archive_files(backup_location):
    """Get blob backup archive files including snapshot files.

    This is only for cleanup.
    """
    return get_blob_backup_archives(
        backup_location, only_timestamps=False, include_snapshot_files=True
    )


# Copy of is_data_file in ZODB / scripts / repozo.py.
is_data_file = re.compile(r"\d{4}(?:-\d\d){5}\.(?:delta)?fsz?$").match


def get_latest_filestorage_timestamp(directory):
    """Get timestamp of latest filestorage backup file in directory.

    Adapted from find_files in ZODB/scripts/repozo.py.

    We can use its timestamp for our blob backup name.
    """
    if not directory or not os.path.isdir(directory):
        logger.debug("Not a directory: %s", directory)
        return
    # newest file first.
    for fname in sorted(os.listdir(directory), reverse=True):
        if not is_data_file(fname):
            continue
        root, ext = os.path.splitext(fname)
        logger.debug("Most recent backup in directory %s is from %s.", directory, root)
        return root
    logger.debug("No data files found in directory: %s", directory)


def get_full_filestorage_timestamp(directory, timestamp=None):
    """Get timestamp of full filestorage backup file in directory.

    When timestamp is None, we return the oldest.
    We can remove any older blob backups.

    With a specific timestamp, we return the timestamp of the
    full backup belonging to this timestamp.

    Adapted from find_files in ZODB/scripts/repozo.py.
    """
    if not directory or not os.path.isdir(directory):
        return
    # oldest first
    found = None
    for fname in sorted(os.listdir(directory)):
        if not is_data_file(fname):
            continue
        root, ext = os.path.splitext(fname)
        if ext not in (".fs", ".fsz"):
            # We are not interested in deltas.
            continue
        # We have found a timestamp of a full backup.  Now compare it.
        if timestamp is None:
            # Just return the oldest one.
            found = root
            break
        if timestamp >= root:
            found = root
        else:
            break
    return found


def get_actual_snar(directory, base_name, timestamp=None):
    """Get snapshot archive file name.

    It may have exactly this timestamp, or earlier.
    """
    if not directory or not os.path.isdir(directory):
        return
    # oldest first
    found = None
    for fname in sorted(os.listdir(directory)):
        root, ext = os.path.splitext(fname)
        if ext != ".snar":
            continue
        base, stamp = os.path.splitext(root)
        if base != base_name:
            continue
        stamp = stamp[1:]  # remove dot
        if not is_time_stamp(stamp):
            continue
        # We have found a timestamp of a full backup.  Now compare it.
        if timestamp is None:
            # Just return the oldest one.
            found = stamp
            break
        if timestamp >= stamp:
            found = stamp
        else:
            break
    return found


def find_snapshot_archive(
    fs_backup_location, destination, base_name, timestamp, full=False
):
    """Find a snapshot archive (.snar).

    This is a file used by tar --listed-incremental to record where each
    backed up file ended up.

    A snapshot archive must always have the same timestamp
    as the full filestorage backup it belongs to: it has file pointers
    to the full backup and the incremental backups.
    This will usually be the case, but not when you first make a full
    backup, and only later enable incremental_blobs.

    It might not exist yet, but may be created by the upcoming tar command,
    *if* this is a full backup.
    """
    if timestamp is None:
        # Not supported. Programming error? Maybe raise an exception.
        return
    # We want a timestamp belonging to a full backup.
    # Get an initial value.
    if full:
        # The given timestamp seems fine.
        full_stamp = timestamp
    else:
        full_stamp = None
    # Try various ways of getting a better timestamp from the file system.
    if fs_backup_location:
        full_stamp = get_full_filestorage_timestamp(fs_backup_location, timestamp)
        if full_stamp is None:
            # There is no proper Data.fs backup belonging to the timestamp.
            # We must return None, as incrementals have no use here.
            return
    elif not full:
        # We are only backing up blobs, and no Data.fs.
        # Look for actual snar files then, but only when we are not
        # explicitly making a full backup.
        full_stamp = get_actual_snar(destination, base_name, timestamp)
        if full_stamp is None:
            # This is the first backup since activating incrementals,
            # so we fall back to the given timestamp.
            full_stamp = timestamp

    # We have determined a full timestamp, so now we can get a file name.
    snapshot_archive = os.path.join(destination, f"{base_name}.{full_stamp}.snar")
    # If the time stamps are the same, then a full backup is in progress.
    # This can be when full is explicitly true, or when a zeopack has made
    # the previous full backup outdated.
    if timestamp != full_stamp and not os.path.exists(snapshot_archive):
        # This message should only get shown during backup, not during
        # restore. But during restore it can only happen if a .snar file
        # has been removed, which seems unlikely.
        logger.warning(
            "Not making incremental blob backup, because this is a "
            "partial backup, and there is no snapshot file yet. "
            "Incremental backups will be created with the next full backup."
        )
        return
    return snapshot_archive


def backup_blobs(
    source,
    destination,
    full=False,
    use_rsync=True,
    keep=0,
    keep_blob_days=0,
    archive_blob=False,
    rsync_options="",
    timestamps=False,
    fs_backup_location=None,
    compress_blob=False,
    incremental_blobs=False,
    rsync_hard_links_on_first_copy=False,
):
    """Copy blobs from source to destination.

    Source is usually something like var/blobstorage and destination
    would be var/blobstoragebackups.  Within that destination we
    create a subdirectory with a fresh blob backup from the source.

    We can make a full backup or a partial backup.  Partial backups
    are done with rsync and hard links to safe disk space.  Actually,
    full backups used to avoid the hard links, but that did not really
    have any extra value, so now it does the same thing, just in its
    own directory.

    With 'use_rsync' at the default True, we use rsync to copy,
    otherwise we use shutil.copytree.  This is mostly there for
    systems that don't have rsync available.  rsync is recommended.

    Note that we end up with something like var/blobstorage copied to
    var/blobbackups/blobstorage.0/blobstorage.  We could copy the
    contents of var/blobstorage directly to blobstorage.0, but then
    the disk space safing hard links do not work.

    keep_blob_days only makes sense in combination with full=False.
    We then use this to keep the backups created in the last
    'keep_blob_days' days.  For full backups we use 'keep' to simply
    keep the last X backups.  But for partial backups 'keep' should
    mean we keep the last X full Data.fs backups plus the partial
    backups created by repozo; and there is no similar concept in our
    blobstorage backups.

    With timestamps True, we do not make blobstorage.0, but use timestamps,
    for example blobstorage.2017-01-02-03-04-05.

    For tests, see tests/backup_blobs_dir.rst.
    """
    source = source.rstrip(os.sep)
    base_name = os.path.basename(source)

    if archive_blob:
        backup_blobs_archive(
            source,
            destination,
            keep,
            timestamps=timestamps,
            fs_backup_location=fs_backup_location,
            compress_blob=compress_blob,
            incremental_blobs=incremental_blobs,
            full=full,
        )
        return

    if timestamps:
        current_backups = get_blob_backup_dirs(destination)
        if current_backups:
            prev = current_backups[0][2]
        else:
            prev = None
        timestamp = get_latest_filestorage_timestamp(fs_backup_location)
        if timestamp:
            dest = os.path.join(destination, base_name + "." + timestamp)
            # if a backup already exists, then apparently there were no
            # database changes since the last backup, so we don't need
            # to do anything.
            if os.path.exists(dest):
                logger.info(
                    "Blob backup at %s already exists, so there were "
                    "no database changes since last backup.",
                    dest,
                )
                # Now possibly remove old backups and remove/create latest symlink.
                if incremental_blobs:
                    latest = None
                else:
                    # Creating a symlink to the latest blob backup only makes sense in this combination.
                    latest = dest
                cleanup(
                    destination,
                    full,
                    keep,
                    keep_blob_days,
                    fs_backup_location=fs_backup_location,
                    latest=latest,
                )
                return
        else:
            dest = os.path.join(destination, base_name + "." + gen_timestamp())
    else:
        # Without timestamps we need to rotate backups.
        rotate_directories(destination, base_name)
        prev = os.path.join(destination, base_name + ".1")
        dest = os.path.join(destination, base_name + ".0")
    if use_rsync:
        if prev and os.path.exists(prev):
            # Make a 'partial' backup by reusing the previous backup.  We
            # might not want to do this for full backups, but this is a
            # lot faster and the end result really is the same, so why
            # not.
            if not os.path.isdir(prev):
                # Should have been caught already.
                raise Exception(f"{prev} must be a directory")
            # Hardlink against the previous directory.  Done by hand it
            # would be:
            # rsync -a  --delete --link-dest=../blobstorage.1 blobstorage/
            #     backups/blobstorage.0
            prev_link = os.path.relpath(prev, dest)
            cmd = (
                "rsync -a {options} --delete --link-dest={link} {source} "
                "{dest}".format(
                    options=rsync_options, link=prev_link, source=source, dest=dest
                )
            )
        else:
            # No previous directory to hardlink against.
            if rsync_hard_links_on_first_copy:
                abs_source = os.path.sep.join((os.path.abspath(source), ""))
                abs_dest = os.path.sep.join((os.path.abspath(dest), base_name, ""))
                os.makedirs(abs_dest, exist_ok=True)
                # Let's hard link against the original one
                cmd = "rsync -a {options} --link-dest={source} {source} {dest}".format(
                    options=rsync_options, source=abs_source, dest=abs_dest
                )
            else:
                cmd = "rsync -a {options} {source} {dest}".format(
                    options=rsync_options, source=source, dest=dest
                )
        logger.info(cmd)
        output, failed = utils.system(cmd)
        if output:
            print(output)
        if failed:
            return
    else:
        if not os.path.exists(dest):
            # The parent directory must exist for shutil.copytree
            # in python2.4.
            os.makedirs(dest)
        target = os.path.join(dest, base_name)
        logger.info("Copying %s to %s", source, target)
        shutil.copytree(source, target)
    # Now possibly remove old backups and remove/create latest symlink.
    if timestamps and not incremental_blobs:
        # Creating a symlink to the latest blob backup only makes sense in this combination.
        latest = dest
    else:
        latest = None
    cleanup(
        destination,
        full,
        keep,
        keep_blob_days,
        fs_backup_location=fs_backup_location,
        latest=latest,
    )


def find_timestamped_filename(destination, filename):
    # compress_blob may be on now, or may have been on in the past.
    # Look for both.  And look for deltas too.
    for suffix in ("tar", "tar.gz", "delta.tar", "delta.tar.gz"):
        fname = f"{filename}.{suffix}"
        dest = os.path.join(destination, fname)
        # If a backup already exists, then apparently there were no
        # database changes since the last backup, so we don't need
        # to do anything.
        if os.path.exists(dest):
            logger.info(
                "Blob backup at %s already exists, so there were "
                "no database changes since last backup.",
                dest,
            )
            return dest


def backup_blobs_archive(
    source,
    destination,
    keep=0,
    timestamps=False,
    fs_backup_location=None,
    compress_blob=False,
    incremental_blobs=False,
    full=False,
):
    """Make archive from blobs in source directory.

    Source is usually something like var/blobstorage and destination
    would be var/blobstoragebackups.  Within that destination we
    create an archive file with a fresh blob backup from the source.

    We use 'keep' to simply keep the last X backups.

    For tests, see tests/backup_blobs_archive.rst.
    """
    if incremental_blobs and not timestamps:
        # This should have been caught by buildout already,
        # but we may trigger it in tests.
        raise Exception("Cannot have incremental_blobs without timestamps.")
    source = source.rstrip(os.sep)
    base_name = os.path.basename(source)
    if not os.path.exists(destination):
        os.makedirs(destination)
    tar_options = ""
    if timestamps:
        timestamp = get_latest_filestorage_timestamp(fs_backup_location)
        if timestamp:
            filename = f"{base_name}.{timestamp}"
            dest = find_timestamped_filename(destination, filename)
            if dest:
                # We have found an existing backup.
                # Now possibly remove old backups and remove/create latest symlink.
                if incremental_blobs:
                    latest = None
                else:
                    # Creating a symlink to the latest blob backup only makes sense in this combination.
                    latest = dest
                cleanup_archives(
                    destination,
                    keep=keep,
                    fs_backup_location=fs_backup_location,
                    latest=latest,
                )
                return
        else:
            timestamp = gen_timestamp()
            filename = f"{base_name}.{timestamp}"
        if incremental_blobs:
            # Get the timestamp of the latest full backup,
            # if we have a snapshot archive for it.
            snapshot_archive = find_snapshot_archive(
                fs_backup_location, destination, base_name, timestamp, full=full
            )
            if snapshot_archive is not None:
                # We need to use the raw format, otherwise
                # '--listed-incremental=/dir' gets normalized to '/dir'
                # by zc.buildout during testing. Strange, but it should
                # be no problem to have quotes here.
                tar_options = f"--listed-incremental={snapshot_archive!r}"
                if os.path.exists(snapshot_archive):
                    # The snapshot archive exists, so this is a delta backup.
                    # File name should be blobs.timestamp.delta.tar(.gz).
                    filename += ".delta"
        filename += ".tar"  # .gz may be added a few lines later.
        dest = os.path.join(destination, filename)
    else:
        # Without timestamps we need to rotate backups.
        rotate_archives(destination, base_name)
        dest = os.path.join(destination, base_name + ".0.tar")
    if compress_blob:
        dest += ".gz"
        tar_command = "tar czf"
    else:
        tar_command = "tar cf"
    if os.path.exists(dest):
        raise Exception(f"Path already exists: {dest}")
    cmd = f"{tar_command} {dest} {tar_options} -C {source} ."
    logger.info(cmd)
    output, failed = utils.system(cmd)
    if output:
        print(output)
    if failed:
        return
    # Now possibly remove old backups and remove/create latest symlink.
    if timestamps and not incremental_blobs:
        # Creating a symlink to the latest blob backup only makes sense in this combination.
        latest = dest
    else:
        latest = None
    cleanup_archives(
        destination, keep=keep, fs_backup_location=fs_backup_location, latest=latest
    )


def is_full_tarball(path):
    """Is this a full tarball?

    We do not care if there are deltas belonging to this tarball.
    """
    if ".delta." in path:
        return False
    if path.endswith(".tar") or path.endswith(".tar.gz"):
        return True
    return False


def is_snar(path):
    """Is this a snapshot archive file?"""
    return path.endswith(".snar")


def is_delta(path):
    """Is this a delta archive file?"""
    return ".delta." in path


def combine_backups(backups):
    """Combine deltas, tars and snars that belong together.

    Return a list of lists.
    This is only useful for archives.
    It is used to see which files can be deleted.
    Really, it is only useful if you backup blobs without filestorage,
    because with filestorage we can simply look for orphaned blobs.

    Note: the most recent backup is listed first.
    We assume the sort order is correct.
    So in case of incrementals, we get:
    delta 2, delta 1, tar, snar.
    Or delta 2, delta 1, snar, tar...
    Without incrementals it may be tar, tar, tar.
    There may be gzips.
    Or it may be directory names.
    Or a combination of all of the above.
    """
    if not backups:
        return []
    # This function is only useful if there are incremental archives.
    has_incremental = any([1 for x in backups if is_snar(x[2]) or is_delta(x[2])])
    if not has_incremental:
        # Put each item in a separate list.
        result = []
        for num, mod_time, path in backups:
            result.append([(num, mod_time, path)])
        return result
    result = [[]]
    for num, mod_time, path in backups:
        current = (num, mod_time, path)
        # Does this belong to the previous one?
        previous = result[-1]
        if not previous:
            # obviously not
            previous.append(current)
            continue
        if os.path.isdir(path):
            # A directory is always on its own.
            result.append([current])
            continue
        # So we have a previous list, and the current item is a file.
        # Does the previous list have a tarball?
        has_tar = any([1 for x in previous if is_full_tarball(x[2])])
        # And a snapshot archive file?
        has_snar = any([1 for x in previous if is_snar(x[2])])
        if has_tar and has_snar:
            # Must be the beginning of a new list.
            result.append([current])
            continue
        if is_delta(path) and (has_tar or has_snar):
            # Must be an older delta, so start a new list.
            result.append([current])
            continue
        if path.endswith(".snar"):
            if has_snar:
                # Strange.  Start a new list.
                previous = []
                result.append(previous)
            elif has_tar:
                pass
            previous.append(current)
            continue
        if is_full_tarball(path):
            # Does the previous list have a tarball?
            if has_tar:
                # Yes, so we start a new list.
                result.append([])
                previous = result[-1]
            previous.append(current)
            continue
        # We should have only deltas now.
        if ".delta." not in path:
            logger.warning("Expected .delta. in path %r.", path)
            # This at least happens in tests, when using names
            # for directories that do not exist.
            # Best to keep this separate.
            result.append([current])
            continue
        previous.append(current)

    # Filter out any empty lists.
    result = [x for x in result if x]
    return result


def find_conditional_backups_to_restore(backups, tester=None):
    # We could get deltas, and then we should return several,
    # so we keep a list.
    paths = []
    # Note: the most recent backup is listed first.
    for num, mod_time, path in backups:
        if tester is not None and not tester(num, mod_time, path):
            continue
        paths.append(path)
        if ".delta." not in path:
            # we have found a full backup
            break
    paths.reverse()
    return paths


def find_backup_to_restore(source, date_string="", archive=False, timestamps=False):
    """Find backup to restore.

    This determines whether blobstorage.0 or blobstorage.1 is taken, etc.

    It may be for a given date string.
    From repozo: specify UTC (not local) time in this format:
    yyyy-mm-dd[-hh[-mm[-ss]]]
    Note that this matches the 2011-10-05-12-12-45.fsz that is created.

    It may be archive backups only (tar or tar.gz).
    If timestamps is True, we prefer those.

    We return nothing or a directory or file name.
    It may be a list in case of delta archives.
    """
    if archive:
        backup_getter = get_blob_backup_archives
    else:
        backup_getter = get_blob_backup_dirs
    current_backups = backup_getter(source)
    if not current_backups:
        return
    if not date_string:
        # The most recent is the default.
        return find_conditional_backups_to_restore(current_backups)

    # We want the backup for a specific date.
    try:
        date_args = [int(num) for num in date_string.split("-")]
    except (AttributeError, ValueError, TypeError):
        logger.error("Could not parse date argument to restore blobs: %r", date_string)
        return
    # Is this a valid datetime?  So not for example 99 seconds?
    target_datetime = datetime(*date_args)

    # repozo restore tries to find the first full backup at or before
    # the specified date, and fails if it cannot be found.
    # We should do the same.  The timestamp of the filestorage and
    # blobstorage backups may be a few seconds apart.  If the user
    # specifies a timestamp in between, this is an error of the user.
    if timestamps:
        ts_backups = backup_getter(source, only_timestamps=True)

        def tester(num, mod_time, directory):
            # Both num and date_string are timestamps, so we can compare them.
            return num <= date_string

        paths = find_conditional_backups_to_restore(ts_backups, tester)
        if paths:
            return paths

    # If timestamps are not used, or do not give a result,
    # we fall back to comparing modification times.
    # Note that in tests, the modification times will be very close together.
    def tester(num, mod_time, directory):
        backup_time = datetime.utcfromtimestamp(mod_time)
        return backup_time <= target_datetime

    paths = find_conditional_backups_to_restore(current_backups, tester)
    if paths:
        return paths


def restore_blobs(
    source,
    destination,
    use_rsync=True,
    date=None,
    archive_blob=False,
    rsync_options="",
    timestamps=False,
    only_check=False,
    incremental_blobs=False,
):
    """Restore blobs from source to destination.

    With 'use_rsync' at the default True, we use rsync to copy,
    otherwise we use shutil.copytree.  This is mostly there for
    systems that don't have rsync available.  rsync is recommended.

    We could remove the destination first (with
    'shutil.rmtree(destination)'), but an 'rsync -a  --delete' works
    faster.

    Note that trailing slashes in source and destination do matter, so
    be careful with that otherwise you may end up with something like
    var/blobstorage/blobstorage

    If only_check is True, we only perform checks.
    Most importantly: check if the backup exists.
    It is not meant as a dry run: we might create a missing directory,
    which serves as a check that the user is allowed to do this.

    The idea is to first call this with only_check=True, and do the same for
    restore_blobs.  When all is well, call it normally without only_check.

    """
    destination = destination.rstrip(os.sep)
    # The archive_blob options may have first been false when creating
    # a backup, then true, then false again.  During restore, we should
    # be able to restore all.
    # See https://github.com/collective/collective.recipe.backup/issues/44

    # Determine the source (blob backup) that should be restored.
    archive_source = find_backup_to_restore(
        source, date_string=date, archive=True, timestamps=timestamps
    )
    standard_source = find_backup_to_restore(
        source, date_string=date, timestamps=timestamps
    )
    if not (standard_source or archive_source):
        # error
        if date:
            logger.error("Could not find backup of %r or earlier.", date)
        else:
            logger.error("There are no backups in %s.", source)
        return True
    # From here on we do have an archive.
    if only_check:
        # We are done.
        return

    if archive_blob and archive_source:
        # We want an archive and have found an archive.
        result = restore_blobs_archive(
            source, destination, date, timestamps=timestamps, only_check=only_check
        )
        return result

    # We either do not want an archive or do not have an archive.
    # So we restore the standard.
    backup_source = standard_source
    if not backup_source:
        return True
    # We probably get a list of one.  For tar archives there may be more,
    # but that does not happen for us.
    if isinstance(backup_source, list):
        if len(backup_source) > 1:
            logger.error(
                "Got %d backup directories to restore, which is more than 1, "
                "which makes no sense: %r",
                len(backup_source),
                backup_source,
            )
            sys.exit(1)
        backup_source = backup_source[0]
    if only_check:
        return

    # We have .../blobstorage.0 as backup source, but we need the destination
    # directory name in it, so usually .../blobstorage.0/blobstorage
    dest_dir = os.path.dirname(destination)
    base_name = os.path.basename(destination)
    backup_source = os.path.join(backup_source, base_name)

    # You should end up with something like this:
    # rsync -a  --delete var/blobstoragebackups/blobstorage.0/blobstorage var/
    if use_rsync:
        cmd = "rsync -a {options} --delete {source} {dest}".format(
            options=rsync_options, source=backup_source, dest=dest_dir
        )
        logger.info(cmd)
        output, failed = utils.system(cmd)
        if output:
            print(output)
        if failed:
            return
    else:
        if os.path.exists(destination):
            logger.info("Removing %s", destination)
            shutil.rmtree(destination)
        logger.info("Copying %s to %s", backup_source, destination)
        shutil.copytree(backup_source, destination)


def restore_blobs_archive(
    source,
    destination,
    date=None,
    timestamps=False,
    only_check=False,
    incremental_blobs=False,
):
    """Restore blobs from source to destination.

    Prepare backup for test:

    >>> mkdir('blobs')
    >>> write('blobs', 'one.txt', 'File One')
    >>> write('blobs', 'two.txt', 'File Two')
    >>> write('blobs', 'three.txt', 'File Three')
    >>> mkdir('blobs', 'dir')
    >>> mkdir('backups')
    >>> backup_blobs_archive('blobs', 'backups', keep=2)
    >>> ls('backups')
    -  blobs.0.tar


    Test restore:

    >>> remove('blobs')
    >>> restore_blobs_archive('backups', 'blobs')
    >>> ls('blobs')
    d  dir
    -  one.txt
    -  three.txt
    -  two.txt

    Test restore of compressed archive.

    >>> write('blobs', 'four.txt', 'File Four')
    >>> backup_blobs_archive('blobs', 'backups', keep=2, compress_blob=True)
    >>> ls('backups')
    -  blobs.0.tar.gz
    -  blobs.1.tar
    >>> remove('blobs')
    >>> restore_blobs_archive('backups', 'blobs')
    >>> ls('blobs')
    d  dir
    -  four.txt
    -  one.txt
    -  three.txt
    -  two.txt

    Cleanup:

    >>> remove('blobs')
    >>> remove('backups')

    """
    # Determine the source (blob backup) that should be restored.
    backup_sources = find_backup_to_restore(
        source, date_string=date, archive=True, timestamps=timestamps
    )
    if not backup_sources:
        # Signal error by returning a true value.
        return True
    if only_check:
        return
    if os.path.exists(destination):
        logger.info("Removing %s", destination)
        shutil.rmtree(destination)
    os.mkdir(destination)
    tar_options = ""
    if not isinstance(backup_sources, list):
        backup_sources = [backup_sources]
    if len(backup_sources) > 1:
        logger.info("Found %d incremental backups to restore.", len(backup_sources))
        tar_options = " --incremental"
    for backup_source in backup_sources:
        logger.info("Extracting %s to %s", backup_source, destination)
        if backup_source.endswith("gz"):
            tar_command = "tar xzf"
        else:
            tar_command = "tar xf"
        cmd = "{} {}{} -C {}".format(
            tar_command, backup_source, tar_options, destination
        )
        logger.info(cmd)
        output, failed = utils.system(cmd)
        if output:
            print(output)
        if failed:
            return True


def remove_orphaned_blob_backups(backup_location, fs_backup_location, archive=False):
    """Remove orphaned blob backups.

    This means: blob backups that have a timestamp older than the oldest
    filestorage backup.

    Returns True when nothing is left to do for any other code
    that might want to do cleanup.
    """
    if not fs_backup_location:
        return
    oldest_timestamp = get_full_filestorage_timestamp(fs_backup_location)
    if not oldest_timestamp:
        return
    logger.debug(
        "Removing blob backups with timestamp before %s from %s",
        oldest_timestamp,
        backup_location,
    )
    if archive:
        backup_getter = get_blob_backup_all_archive_files
    else:
        backup_getter = get_blob_backup_dirs
    current_backups = backup_getter(backup_location)
    if not current_backups:
        # Can't remove what does not exist.
        return True
    deleted = 0
    for num, mod_time, directory in current_backups:
        if is_time_stamp(num):
            if num >= oldest_timestamp:
                continue
        else:
            # blobstorage.0/1/2
            if gen_timestamp(mod_time) >= oldest_timestamp:
                continue
        if archive:
            # It is actually a file.
            os.remove(directory)
        else:
            shutil.rmtree(directory)
        deleted += 1
        logger.debug("Deleted %s.", directory)
    if deleted:
        logger.info(
            "Removed %d blob %s, all backups "
            "belonging to remaining filestorage backups have "
            "been kept.",
            deleted,
            "backup" if deleted == 1 else "backups",
        )
    # We are done.
    return True


def cleanup(
    backup_location,
    full=False,
    keep=0,
    keep_blob_days=0,
    fs_backup_location=None,
    latest=None,
):
    """Clean up old blob backups.

    When fs_backup_location is passed and we find filestorage backups there,
    we ignore the keep and keep_blob_days options.
    We remove any blob backups that are older than the oldest
    filestorage backup.

    For tests, see tests/cleanup_dir.rst.
    """
    update_latest_symlink(backup_location, latest=latest)

    logger.debug("Starting cleanup of blob backups from %s", backup_location)
    if remove_orphaned_blob_backups(backup_location, fs_backup_location):
        # A True return value means there is nothing left to do.
        return

    # Making sure we use integers.
    keep = int(keep)
    keep_blob_days = int(keep_blob_days)
    if full:
        # For full backups we do not need to count days.
        keep_blob_days = 0
    if (not keep) and (not keep_blob_days):
        logger.debug("We do not want to remove anything.")
        return
    if keep_blob_days and not full:
        # For partial backups we ignore the 'keep' in favour of
        # 'keep_blob_days' if that is set, but we do set 'keep' to
        # keep at least one backup (the most recent one) in case our
        # logic somehow fails, like when modification dates have been
        # tampered with.
        keep = 1
    if keep == 0:
        logger.debug("keep=0, so not removing backups.")
        return
    logger.debug("Trying to clean up old backups.")
    backup_dirs = get_blob_backup_dirs(backup_location)
    if full:
        logger.debug("This is a full backup.")
        logger.debug("Max number of backups: %d.", keep)
        logger.debug("Number of blob days to keep: %d (ignored).", keep_blob_days)
    else:
        logger.debug("This is a partial backup.")
        logger.debug("Minimum number of backups to keep: %d.", keep)
        logger.debug("Number of blob days to keep: %d.", keep_blob_days)
    if len(backup_dirs) <= keep:
        logger.debug("Not removing backups.")
        return
    logger.debug("There are older backups that we can remove.")
    remove = backup_dirs[keep:]
    logger.debug("Will possibly remove: %r", remove)
    deleted = 0
    now = time.time()
    for num, mod_time, directory in remove:
        if keep_blob_days:
            mod_days = (now - mod_time) / 86400  # 24 * 60 * 60
            if mod_days < keep_blob_days:
                # I'm too young to die!
                continue
        shutil.rmtree(directory)
        deleted += 1
        logger.debug("Deleted %s.", directory)
    if not deleted:
        logger.debug("Nothing removed.")
        return
    if full:
        logger.info(
            "Removed %d blob %s, the latest " "%d %s been kept.",
            deleted,
            "backup" if deleted == 1 else "backups",
            keep,
            "backup has" if keep == 1 else "backups have",
        )
    else:
        logger.info(
            "Removed %d blob %s. The backups of the latest " "%d %s been kept.",
            deleted,
            "backup" if deleted == 1 else "backups",
            keep_blob_days,
            "day has" if keep_blob_days == 1 else "days have",
        )


def update_latest_symlink(backup_location, latest=None):
    """Update symlink to latest blob backup."""
    # Remove symlink to the latest blob backup.
    cwd = os.getcwd()
    os.chdir(backup_location)
    symlink = "latest"
    if os.path.islink(symlink):
        logger.debug(
            "Removed old symlink latest pointing to %s", os.path.realpath(symlink)
        )
        os.unlink(symlink)
    if latest:
        latest = os.path.basename(latest)
        # This may recreate the symlink we previously removed, but okay.
        logger.info("Creating symlink from latest to %s", latest)
        os.symlink(latest, symlink)
    # back to where we came from
    os.chdir(cwd)


def cleanup_archives(backup_location, keep=0, fs_backup_location=None, latest=None):
    """Clean up old blob backups.

    When fs_backup_location is passed and we find filestorage backups there,
    we ignore the keep and keep_blob_days options.
    We remove any blob backups that are older than the oldest
    filestorage backup.

    For tests, see tests/cleanup_archives.rst.
    """
    update_latest_symlink(backup_location, latest=latest)

    logger.debug("Starting cleanup of blob archives from %s", backup_location)
    if remove_orphaned_blob_backups(backup_location, fs_backup_location, archive=True):
        # A True return value means there is nothing left to do.
        return

    # Making sure we use integers.
    keep = int(keep)
    if keep == 0:
        logger.debug("keep=0, so not removing backups.")
        return
    logger.debug("Trying to clean up old backups.")
    backup_archives = get_blob_backup_all_archive_files(backup_location)
    combined_archives = combine_backups(backup_archives)
    logger.debug("Max number of backups: %d.", keep)
    if len(combined_archives) <= keep:
        logger.debug("Not removing backups.")
        return
    logger.debug("There are older backups that we can remove.")
    remove = combined_archives[keep:]
    logger.debug("Will remove: %r", remove)
    deleted_full = 0
    deleted_files = 0
    for archive in remove:
        for num, mod_time, archive_file in archive:
            os.remove(archive_file)
            deleted_files += 1
            logger.debug("Deleted %s.", archive_file)
        deleted_full += 1
    logger.info(
        "Removed %d full blob %s, with %d %s. " "The latest %d %s been kept.",
        deleted_full,
        "backup" if deleted_full == 1 else "backups",
        deleted_files,
        "file" if deleted_files == 1 else "files",
        keep,
        "backup has" if keep == 1 else "backups have",
    )
