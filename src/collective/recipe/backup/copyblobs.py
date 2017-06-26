"""
The idea is to use rsync and hard links; this probably requires a
unixy (Linux, Mac OS X) operating system.

It is based on this article by Mike Rubel:
http://www.mikerubel.org/computers/rsync_snapshots/
"""

from collective.recipe.backup import utils
from datetime import datetime
from operator import itemgetter

import logging
import os
import re
import shutil
import sys
import time


logger = logging.getLogger('blobs')
SOURCE = 'blobstorage'
BACKUP_DIR = 'backups'
# Similar to is_data_file in repozo.py:
is_time_stamp = re.compile(r'\d{4}(?:-\d\d){5}$').match


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
        if isinstance(suffixes, basestring):
            suffixes = [suffixes]
        found = False
        for suffix in suffixes:
            if not suffix.startswith('.'):
                suffix = '.' + suffix
            if value.endswith(suffix):
                found = True
                break
        if not found:
            return
        value = value[:-len(suffix)]
    if prefix is None:
        # number or anything.number.
        # But 'anything' should not contain dots: too tricky.
        dots = value.count('.')
        if dots > 1:
            return
        if dots == 1:
            prefix, value = value.split('.')
        else:
            prefix = ''
    else:
        # A dot at the end would be a coding error.
        if not prefix.endswith('.'):
            prefix += '.'
        if not value.startswith(prefix):
            return
        value = value[len(prefix):]
    # At this point, we really should only have a number left.
    try:
        int(value)
    except ValueError:
        if not is_time_stamp(value):
            return
    if prefix:
        # return prefix without dot
        prefix = prefix.rstrip('.')
    return prefix, value


def strict_cmp_numbers(a, b):
    """Compare backup numbers, sorting newest first.

    a and b MUST be strings with either an integer or a timestamp.
    So '0', '1', '1999-12-31-23-59-30'.

    Comparing integers:
    The smallest integer in a comparison gets -1.
    Example: 0, 1, 2.

    Comparing timestamps:
    The biggest timestamp gets -1.
    Example: 2000-12-31-23-59-30, 1999-12-31-23-59-30.

    If integers and timestamps are compared, timestamps are always smaller:
    1999-12-31-23-59-30, 0, 1.
    """
    # Check if one or both are timestamps.
    a_time_stamp = None
    b_time_stamp = None
    try:
        a = int(a)
    except ValueError:
        if not is_time_stamp(a):
            raise ValueError('No integer and no timestamp in {0}.'.format(a))
        a_time_stamp = a
    try:
        b = int(b)
    except ValueError:
        if not is_time_stamp(b):
            raise ValueError('No integer and no timestamp in {0}.'.format(b))
        b_time_stamp = b

    # Now choose the right comparison.
    if a_time_stamp is None and b_time_stamp is None:
        # Both are integers.
        return cmp(a, b)
    if a_time_stamp is not None and b_time_stamp is not None:
        # Both are timestamps.  The biggest must be first,
        # so we switch the comparison around.
        return cmp(b_time_stamp, a_time_stamp)
    # From here on, one is an integer, the other a timestamp.
    if a_time_stamp is None:
        # a is an integer, so a is bigger than b.
        return 1
    # b is a timestamp, so a is smaller.
    return -1


def strict_cmp_backups(a, b):
    """Compare backups.

    a and b MUST be something like blobstorage.0 and
    blobstorage.1, which should be sorted numerically.

    New is that it may also be  a timestamp like
    blobstorage.1999-12-31-23-59-30.

    Newest must be first: x.0, x.1, x.2.
    This means that the smallest integer in a comparison gets -1.
    The biggest timestamp gets -1.

    If integers and timestamps are compared, timestamps are always smaller:
    x.timestamp, x.0, x.1.
    """
    assert '.' in a
    assert '.' in b
    a_start, a_num = a.rsplit('.', 1)
    b_start, b_num = b.rsplit('.', 1)
    if a_start != b_start:
        raise ValueError(
            "Not the same start for backups: %r vs %r" % (a, b))
    return strict_cmp_numbers(a_num, b_num)


def strict_cmp_gzips(a, b):
    """Compare backups.

    a and b MUST be something like blobstorage.0.tar.gz and
    blobstorage.1.tar.gz, which should be sorted numerically.

    """
    suffixes = ['.tar', '.tar.gz']
    cleaned = []
    for candidate in (a, b):
        correct = False
        for suffix in suffixes:
            if candidate.endswith(suffix):
                correct = True
                cleaned.append(candidate[:-len(suffix)])
                break
        if not correct:
            raise ValueError('{0} does not end with {1}'.format(
                candidate, suffix))
    return strict_cmp_backups(*cleaned)


def gen_timestamp(now=None):
    """Generate timestamp.

    With 'now' you can set a different time for testing.
    It should be a tuple of year, month, day, hour, minute, second.
    A number (like time.time()) works too.
    """
    if now is None or isinstance(now, (int, float)):
        now = time.gmtime(now)[:6]
    return '%04d-%02d-%02d-%02d-%02d-%02d' % now


def gen_blobdir_name(prefix='blobstorage', now=None):
    """Generate directory name for blobstorage.

    This is adapted from gen_filename from ZODB/scripts/repozo.py.

    With 'now' you can set a different time for testing.
    It should be a tuple of year, month, day, hour, minute, second.
    """
    if now is None:
        now = time.gmtime()[:6]
    t = now
    ts = gen_timestamp(t)
    return '{0}.{1}'.format(prefix, ts)


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

    >>> write('dirtest', 'a.3', "Test file.")
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
    for entry in os.listdir(container):
        if not entry.startswith(name + '.'):
            continue
        entry_start, entry_num = entry.rsplit('.', 1)
        if entry_start != name:
            # Maybe something like 'blobstorage.break.me.0'
            logger.warn("Ignoring entry %s in %s", entry, container)
            continue
        try:
            entry_num = int(entry_num)
        except (ValueError, TypeError):
            continue
        # Looks like we have a winner.  It must be a directory though.
        if not os.path.isdir(os.path.join(container, entry)):
            raise Exception("Refusing to rotate %s as it is not a directory." %
                            entry)
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
    ...     write('dirtest', gz, "Test file.")
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
    for entry in os.listdir(container):
        matched = re.match("^%s\.(\d+)\.tar(\.gz)?$" % name, entry)
        if matched is None:
            continue
        match = matched.groups()[0]
        try:
            int(match)
        except (ValueError, TypeError):
            continue
        if not os.path.isfile(os.path.join(container, entry)):
            raise Exception("Refusing to rotate %s as it is not a file." %
                            entry)
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
    sorted_backups = sorted(previous_backups, cmp=strict_cmp_backups,
                            reverse=True)
    # Rotate the directories.
    for directory in sorted_backups:
        new_num = int(directory.split('.')[-1]) + 1
        new_name = '%s.%s' % (name, new_num)
        logger.info("Renaming %s to %s.", directory, new_name)
        os.rename(os.path.join(container, directory),
                  os.path.join(container, new_name))


def rotate_archives(container, name):
    """Rotate archive files in container that start with 'name'.

    Both tar and tar.gz are accepted.

    Note: timestamps are not handled here.  This function is not used
    in scenarios that use timestamps.

    Using the zc.buildout tools we create some directories and files:

    >>> mkdir('dirtest')
    >>> rotate_archives('dirtest', 'a')
    >>> for gz in ['a.0.tar', 'a.1.tar.gz', 'a.2.tar', 'a.9.tar.gz']:
    ...     write('dirtest', gz, "File content.")
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
    sorted_backups = sorted(previous_backups, cmp=strict_cmp_gzips,
                            reverse=True)
    # Rotate the directories.
    for entry in sorted_backups:
        matched = re.match("^%s\.(\d+)\.tar(\.gz)?$" % name, entry)
        old_num, gz = matched.groups()
        new_num = int(old_num) + 1
        if gz is None:
            gz = ""
        new_name = "%s.%s.tar%s" % (name, new_num, gz)
        logger.info("Renaming %s to %s.", entry, new_name)
        os.rename(os.path.join(container, entry),
                  os.path.join(container, new_name))


def get_blob_backup_dirs(backup_location, only_timestamps=False):
    """Get blob backup dirs from this location.

    If only_timestamps is True, we only return backups that have timestamps.
    That is useful when restoring.
    """
    filenames = os.listdir(backup_location)
    logger.debug("Looked up filenames in the target dir: %s found. %r.",
                 len(filenames), filenames)
    backup_dirs = []
    prefix = ''
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
                    "exit, because we cannot get a correct sort order." % (
                        backup_location, prefix, parts[0]))
                sys.exit(1)
        else:
            prefix = parts[0]
        mod_time = os.path.getmtime(full_path)
        backup_dirs.append((num, mod_time, full_path))
    # We always sort by backup number:
    backup_dirs = sorted(
        backup_dirs, key=itemgetter(0), cmp=strict_cmp_numbers)
    # Check if this is the same as reverse sorting by modification time:
    mod_times = sorted(backup_dirs, key=itemgetter(1), reverse=True)
    if backup_dirs != mod_times:
        logger.warn("Sorting blob backups by number gives other result than "
                    "reverse sorting by last modification time.")
    logger.debug("Found %d blob backups: %r.", len(backup_dirs),
                 [d[1] for d in backup_dirs])
    return backup_dirs


def get_blob_backup_archives(backup_location, only_timestamps=False):
    """Get blob backup archive files from this location.

    Archives may be .tar or .tar.gz files.  We return both.

    If only_timestamps is True, we only return backups that have timestamps.
    That is useful when restoring.
    """
    filenames = os.listdir(backup_location)
    logger.debug("Looked up filenames in the target dir: %s found. %r.",
                 len(filenames), filenames)
    backup_archives = []
    suffixes = ['tar', '.tar.gz']
    prefix = ''
    for filename in filenames:
        # We only want files of the form prefix.X.tar.gz, where X is an
        # integer or a timestamp.  There should not be anything else,
        # but we like to be safe.
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
                    "exit, because we cannot get a correct sort order." % (
                        backup_location, prefix, parts[0]))
                sys.exit(1)
        else:
            prefix = parts[0]

        mod_time = os.path.getmtime(full_path)
        backup_archives.append((num, mod_time, full_path))

    # We always sort by backup number:
    backup_archives = sorted(
        backup_archives, key=itemgetter(0), cmp=strict_cmp_numbers)

    # Check if this is the same as reverse sorting by modification time:
    mod_times = sorted(backup_archives, key=itemgetter(1), reverse=True)

    if backup_archives != mod_times:
        logger.warn("Sorting blob backups by number gives other result than "
                    "reverse sorting by last modification time.")
    logger.debug("Found %d blob backups: %r.", len(backup_archives),
                 [d[1] for d in backup_archives])
    return backup_archives


# Copy of is_data_filein ZODB / scripts / repozo.py.
is_data_file = re.compile(r'\d{4}(?:-\d\d){5}\.(?:delta)?fsz?$').match


def get_latest_filestorage_timestamp(directory):
    """Get timestamp of latest filestorage backup file in directory.

    Adapted from find_files in ZODB/scripts/repozo.py.

    We can use its timestamp for our blob backup name.
    """
    if not directory or not os.path.isdir(directory):
        logger.debug('Not a directory: %s', directory)
        return
    # newest file first.
    for fname in sorted(os.listdir(directory), reverse=True):
        if not is_data_file(fname):
            continue
        root, ext = os.path.splitext(fname)
        logger.debug('Most recent backup in directory %s is from %s.',
                     directory, root)
        return root
    logger.debug('No data files found in directory: %s', directory)


def get_oldest_filestorage_timestamp(directory):
    """Get timestamp of oldest full filestorage backup file in directory.

    Adapted from find_files in ZODB/scripts/repozo.py.

    We can remove any older blob backups.
    """
    if not directory or not os.path.isdir(directory):
        return
    # oldest first
    for fname in sorted(os.listdir(directory)):
        if not is_data_file(fname):
            continue
        root, ext = os.path.splitext(fname)
        if ext in ('.fs', '.fsz'):
            return root


def backup_blobs(source, destination, full=False, use_rsync=True,
                 keep=0, keep_blob_days=0, archive_blob=False, rsync_options='',
                 timestamps=False, fs_backup_location=None,
                 compress_blob=False):
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

    Again, let's test this using the tools from zc.buildout:

    >>> mkdir('blobs')
    >>> write('blobs', 'one.txt', "File One")
    >>> write('blobs', 'two.txt', "File Two")
    >>> write('blobs', 'three.txt', "File Three")
    >>> mkdir('blobs', 'dir')
    >>> mkdir('backups')
    >>> backup_blobs('blobs', 'backups')
    >>> ls('backups')
    d  blobs.0
    >>> ls('backups', 'blobs.0')
    d  blobs
    >>> ls('backups', 'blobs.0', 'blobs')
    d  dir
    -  one.txt
    -  three.txt
    -  two.txt

    Change some stuff.

    >>> write('blobs', 'one.txt', "Changed File One")
    >>> write('blobs', 'four.txt', "File Four")
    >>> remove('blobs', 'two.txt')
    >>> backup_blobs('blobs/', 'backups')
    >>> ls('backups')
    d  blobs.0
    d  blobs.1
    >>> ls('backups', 'blobs.1', 'blobs')
    d  dir
    -  one.txt
    -  three.txt
    -  two.txt
    >>> ls('backups', 'blobs.0', 'blobs')
    d  dir
    -  four.txt
    -  one.txt
    -  three.txt
    >>> cat('backups', 'blobs.1', 'blobs', 'one.txt')
    File One
    >>> cat('backups', 'blobs.0', 'blobs', 'one.txt')
    Changed File One

    Check the file stats to see if they are really hard links:

    >>> import os
    >>> stat_0 = os.stat(os.path.join('backups', 'blobs.0', 'blobs',
    ...                               'three.txt'))
    >>> stat_1 = os.stat(os.path.join('backups', 'blobs.1', 'blobs',
    ...                               'three.txt'))
    >>> stat_0.st_ino == stat_1.st_ino
    True

    Now cleanup and try with filestamps.

    >>> remove('backups')
    >>> mkdir('backups')
    >>> backup_blobs('blobs', 'backups', timestamps=True)
    >>> ls('backups')
    d  blobs.20...-...-...-...-...
    >>> backup0 = os.listdir('backups')[0]
    >>> timestamp0 = backup0[len('blobs.'):]
    >>> ls('backups', backup0, 'blobs')
    d  dir
    -  four.txt
    -  one.txt
    -  three.txt

    Wait a while, so we get a different timestamp, and then change some stuff.

    >>> import time
    >>> time.sleep(1)
    >>> remove('blobs', 'three.txt')
    >>> remove('blobs', 'four.txt')
    >>> backup_blobs('blobs', 'backups', timestamps=True)
    >>> ls('backups')
    d  blobs.20...-...-...-...-...
    d  blobs.20...-...-...-...-...
    >>> backup1 = os.listdir('backups')[-1]
    >>> timestamp1 = backup1[len('blobs.'):]
    >>> timestamp0 < timestamp1
    True
    >>> ls('backups', backup1, 'blobs')
    d  dir
    -  one.txt

    Now we pretend that there is a filestorage backup from the time that
    the most recent backup was made.
    Pass that to the backup_blobs function.
    It should not make a new blob backup, because there is one matching
    the most recent filestorage backup.
    This actually cleans up the oldest backup, because it does not belong
    to any filestorage backup.

    >>> mkdir('fs')
    >>> write('fs', '{0}.fsz'.format(timestamp1), 'dummy fs' )
    >>> backup_blobs('blobs', 'backups', timestamps=True,
    ...     fs_backup_location='fs')
    >>> ls('backups')
    d  blobs.20...-...-...-...-...
    >>> len(os.listdir('backups'))  # The dots could shadow other backups.
    1
    >>> backup1 == os.listdir('backups')[0]
    True
    >>> ls('backups', backup1, 'blobs')
    d  dir
    -  one.txt

    Pretend there is a newer filestorage backup and a blob change.

    >>> write('blobs', 'two.txt', 'File two')
    >>> write('fs', '2100-01-01-00-00-00.fsz', 'dummy fs')
    >>> backup_blobs('blobs', 'backups', timestamps=True,
    ...    fs_backup_location='fs')
    >>> ls('backups')
    d  blobs.20...-...-...-...-...
    d  blobs.2100-01-01-00-00-00
    >>> len(os.listdir('backups'))  # The dots could shadow a third backup
    2
    >>> ls('backups', 'blobs.2100-01-01-00-00-00', 'blobs')
    d  dir
    -  one.txt
    -  two.txt

    Remove the oldest filestorage backup.

    >>> remove('fs', '{0}.fsz'.format(timestamp1))
    >>> backup_blobs('blobs', 'backups', timestamps=True,
    ...    fs_backup_location='fs')
    >>> ls('backups')
    d  blobs.2100-01-01-00-00-00
    >>> len(os.listdir('backups'))
    1

    Cleanup:

    >>> remove('blobs')
    >>> remove('backups')

    We do mostly the same as above, but now using full backups.

    >>> mkdir('blobs')
    >>> write('blobs', 'one.txt', "File One")
    >>> write('blobs', 'two.txt', "File Two")
    >>> write('blobs', 'three.txt', "File Three")
    >>> mkdir('blobs', 'dir')
    >>> mkdir('backups')
    >>> backup_blobs('blobs', 'backups', full=True)
    >>> ls('backups')
    d  blobs.0
    >>> ls('backups', 'blobs.0')
    d  blobs
    >>> ls('backups', 'blobs.0', 'blobs')
    d  dir
    -  one.txt
    -  three.txt
    -  two.txt

    Change some stuff.

    >>> write('blobs', 'one.txt', "Changed File One")
    >>> write('blobs', 'four.txt', "File Four")
    >>> remove('blobs', 'two.txt')
    >>> backup_blobs('blobs', 'backups', full=True)
    >>> ls('backups')
    d  blobs.0
    d  blobs.1
    >>> ls('backups', 'blobs.1', 'blobs')
    d  dir
    -  one.txt
    -  three.txt
    -  two.txt
    >>> ls('backups', 'blobs.0', 'blobs')
    d  dir
    -  four.txt
    -  one.txt
    -  three.txt
    >>> cat('backups', 'blobs.1', 'blobs', 'one.txt')
    File One
    >>> cat('backups', 'blobs.0', 'blobs', 'one.txt')
    Changed File One

    Check the file stats.  We did full copies, but these should still
    be hard links.

    >>> import os
    >>> stat_0 = os.stat(os.path.join('backups', 'blobs.0', 'blobs',
    ...                               'three.txt'))
    >>> stat_1 = os.stat(os.path.join('backups', 'blobs.1', 'blobs',
    ...                               'three.txt'))
    >>> stat_0.st_ino == stat_1.st_ino
    True

    >>> backup_blobs('blobs', 'backups', timestamps=True)
    >>> ls('backups')
    d  blobs.0
    d  blobs.1
    d  blobs.20...

    Cleanup:

    >>> remove('blobs')
    >>> remove('backups')

    """
    source = source.rstrip(os.sep)
    base_name = os.path.basename(source)

    if archive_blob:
        backup_blobs_archive(
            source, destination, keep, timestamps=timestamps,
            fs_backup_location=fs_backup_location,
            compress_blob=compress_blob)
        return

    if timestamps:
        current_backups = get_blob_backup_dirs(destination)
        if current_backups:
            prev = current_backups[0][2]
        else:
            prev = None
        timestamp = get_latest_filestorage_timestamp(fs_backup_location)
        if timestamp:
            dest = os.path.join(destination, base_name + '.' + timestamp)
            # if a backup already exists, then apparently there were no
            # database changes since the last backup, so we don't need
            # to do anything.
            if os.path.exists(dest):
                logger.info('Blob backup at %s already exists, so there were '
                            'no database changes since last backup.', dest)
                # Now possibly remove old backups.
                cleanup(destination, full, keep, keep_blob_days,
                        fs_backup_location=fs_backup_location)
                return
        else:
            dest = os.path.join(destination,
                                base_name + '.' + gen_timestamp())
    else:
        # Without timestamps we need to rotate backups.
        rotate_directories(destination, base_name)
        prev = os.path.join(destination, base_name + '.1')
        dest = os.path.join(destination, base_name + '.0')
    if use_rsync:
        if prev and os.path.exists(prev):
            # Make a 'partial' backup by reusing the previous backup.  We
            # might not want to do this for full backups, but this is a
            # lot faster and the end result really is the same, so why
            # not.
            if not os.path.isdir(prev):
                # Should have been caught already.
                raise Exception("%s must be a directory" % prev)
            # Hardlink against the previous directory.  Done by hand it
            # would be:
            # rsync -a  --delete --link-dest=../blobstorage.1 blobstorage/
            #     backups/blobstorage.0
            prev_link = os.path.relpath(prev, dest)
            cmd = ('rsync -a %(options)s --delete --link-dest=%(link)s '
                   '%(source)s %(dest)s' % dict(
                       options=rsync_options, link=prev_link,
                       source=source, dest=dest))
        else:
            # No previous directory to hardlink against.
            cmd = 'rsync -a %(options)s %(source)s %(dest)s' % dict(
                options=rsync_options, source=source, dest=dest)
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
        dest = os.path.join(dest, base_name)
        logger.info("Copying %s to %s", source, dest)
        shutil.copytree(source, dest)
    # Now possibly remove old backups.
    cleanup(destination, full, keep, keep_blob_days,
            fs_backup_location=fs_backup_location)


def backup_blobs_archive(
    source, destination, keep=0, timestamps=False,
    fs_backup_location=None,
    compress_blob=False,
):
    """Make archive from blobs in source directory.

    Source is usually something like var/blobstorage and destination
    would be var/blobstoragebackups.  Within that destination we
    create an archive file with a fresh blob backup from the source.

    We use 'keep' to simply keep the last X backups.

    Again, let's test this using the tools from zc.buildout:

    >>> mkdir('blobs')
    >>> write('blobs', 'one.txt', "File One")
    >>> write('blobs', 'two.txt', "File Two")
    >>> write('blobs', 'three.txt', "File Three")
    >>> mkdir('blobs', 'dir')
    >>> mkdir('backups')
    >>> backup_blobs_archive('blobs', 'backups', keep=0)
    >>> ls('backups')
    -  blobs.0.tar

    Change some stuff and compress.

    >>> write('blobs', 'one.txt', "Changed File One")
    >>> write('blobs', 'four.txt', "File Four")
    >>> remove('blobs', 'two.txt')
    >>> backup_blobs_archive('blobs/', 'backups', compress_blob=True)
    >>> ls('backups')
    -  blobs.0.tar.gz
    -  blobs.1.tar

    Change some stuff and no longer compress.

    >>> write('blobs', 'one.txt', "Changed File One Again")
    >>> backup_blobs_archive('blobs', 'backups')
    >>> ls('backups')
    -  blobs.0.tar
    -  blobs.1.tar.gz
    -  blobs.2.tar

    Use timestamps with a fs_backup_location.

    >>> mkdir('fs')
    >>> write('fs', '2017-05-24-11-54-39.fsz', "Dummy filestorage backup")
    >>> backup_blobs_archive('blobs', 'backups', fs_backup_location='fs', timestamps=True, compress_blob=True)
    >>> ls('backups')
    -  blobs.0.tar
    -  blobs.1.tar.gz
    -  blobs.2.tar
    -  blobs.2017-05-24-11-54-39.tar.gz

    And again with the same settings, as I saw something go wrong once.

    >>> backup_blobs_archive('blobs', 'backups', fs_backup_location='fs', timestamps=True, compress_blob=True)
    >>> ls('backups')
    -  blobs.0.tar
    -  blobs.1.tar.gz
    -  blobs.2.tar
    -  blobs.2017-05-24-11-54-39.tar.gz

    Same without compressing, which accepts previous compressed tarballs too.

    >>> backup_blobs_archive('blobs', 'backups', fs_backup_location='fs', timestamps=True, compress_blob=False)
    >>> ls('backups')
    -  blobs.0.tar
    -  blobs.1.tar.gz
    -  blobs.2.tar
    -  blobs.2017-05-24-11-54-39.tar.gz

    Same settings, now with a newer filestorage backup.

    >>> write('fs', '2017-05-24-12-00-00.fsz', "Dummy filestorage backup 2")
    >>> backup_blobs_archive('blobs', 'backups', fs_backup_location='fs', timestamps=True, compress_blob=False)
    >>> ls('backups')
    -  blobs.0.tar
    -  blobs.1.tar.gz
    -  blobs.2.tar
    -  blobs.2017-05-24-11-54-39.tar.gz
    -  blobs.2017-05-24-12-00-00.tar

    Cleanup:

    >>> remove('blobs')
    >>> remove('backups')
    >>> remove('fs')
    """
    source = source.rstrip(os.sep)
    base_name = os.path.basename(source)
    if not os.path.exists(destination):
        os.makedirs(destination)
    if timestamps:
        timestamp = get_latest_filestorage_timestamp(fs_backup_location)
        if timestamp:
            filename = base_name + '.' + timestamp + '.tar'
            # compress_blob may be on now, or may have been on in the past.
            # Look for both.
            for fname in (filename, filename + '.gz'):
                dest = os.path.join(destination, fname)
                # If a backup already exists, then apparently there were no
                # database changes since the last backup, so we don't need
                # to do anything.
                if os.path.exists(dest):
                    logger.info(
                        'Blob backup at %s already exists, so there were '
                        'no database changes since last backup.', dest)
                    # Now possibly remove old backups.
                    cleanup_archives(
                        destination, keep=keep,
                        fs_backup_location=fs_backup_location)
                    return
            # Use the .tar filename as initial destination.
            dest = os.path.join(destination, filename)
        else:
            filename = base_name + '.' + gen_timestamp() + '.tar'
            dest = os.path.join(destination, filename)
    else:
        # Without timestamps we need to rotate backups.
        rotate_archives(destination, base_name)
        dest = os.path.join(destination, base_name + '.0.tar')
    if compress_blob:
        dest += '.gz'
        tar_command = "tar czf"
    else:
        tar_command = "tar cf"
    if os.path.exists(dest):
        raise Exception("Path already exists: %s" % dest)
    cmd = "%s %s -C %s ." % (tar_command, dest, source)
    logger.info(cmd)
    output, failed = utils.system(cmd)
    if output:
        print(output)
    if failed:
        return
    # Now possibly remove old backups.
    cleanup_archives(
        destination, keep=keep,
        fs_backup_location=fs_backup_location)


def find_backup_to_restore(source, date_string='', archive=False,
                           timestamps=False):
    """Find backup to restore.

    This determines whether blobstorage.0 or blobstorage.1 is taken, etc.

    It may be for a given date string.
    From repozo: specify UTC (not local) time in this format:
    yyyy-mm-dd[-hh[-mm[-ss]]]
    Note that this matches the 2011-10-05-12-12-45.fsz that is created.

    It may be archive backups only (tar or tar.gz).
    If timestamps is True, we prefer those.

    We return nothing or a directory or file name.
    """
    if archive:
        backup_getter = get_blob_backup_archives
    else:
        backup_getter = get_blob_backup_dirs
    current_backups = backup_getter(source)
    if not current_backups:
        logger.error("There are no backups in %s.", source)
        return
    if not date_string:
        # The most recent is the default.
        # We only need the directory or filename.
        return current_backups[0][2]

    # We want the backup for a specific date.
    try:
        date_args = [int(num) for num in date_string.split('-')]
    except:
        logger.error("Could not parse date argument to restore blobs: %r",
                     date_string)
        return
    # Is this a valid datetime?  So not for example 99 seconds?
    target_datetime = datetime(*date_args)

    # repozo restore tries to find the first full backup at or before
    # the specified date, and fails if it cannot be found.
    # We should do the same.  The timestamp of the filestorage and
    # blobstorage backups may be a few seconds apart.  If the user
    # specifies a timestamp in between, this is an error of the user.
    if timestamps:
        backup_dirs = backup_getter(
            source, only_timestamps=True)
        # Note: the most recent timestamp is listed first.
        for num, mod_time, directory in backup_dirs:
            # Since both num and date are timestamps, we can compare them.
            if num <= date_string:
                return directory

    # Compare modification times.
    backup_dirs = backup_getter(source)
    for num, mod_time, directory in backup_dirs:
        backup_time = datetime.utcfromtimestamp(mod_time)
        if backup_time <= target_datetime:
            return directory

    logger.error("Could not find backup of %r or earlier.", date_string)


def restore_blobs(source, destination, use_rsync=True,
                  date=None, archive_blob=False, rsync_options='',
                  timestamps=False, only_check=False):
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
    if archive_blob:
        result = restore_blobs_archive(
            source, destination, date, timestamps=timestamps,
            only_check=only_check)
        return result

    # Determine the source (blob backup) that should be restored.
    backup_source = find_backup_to_restore(
        source, date_string=date, timestamps=timestamps)
    if not backup_source:
        return True
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
        cmd = 'rsync -a %(options)s --delete %(source)s %(dest)s' % dict(
            options=rsync_options,
            source=backup_source,
            dest=dest_dir)
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


def restore_blobs_archive(source, destination, date=None, timestamps=False,
                       only_check=False):
    """Restore blobs from source to destination.

    Prepare backup for test:

    >>> mkdir('blobs')
    >>> write('blobs', 'one.txt', "File One")
    >>> write('blobs', 'two.txt', "File Two")
    >>> write('blobs', 'three.txt', "File Three")
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

    >>> write('blobs', 'four.txt', "File Four")
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
    backup_source = find_backup_to_restore(
        source, date_string=date, archive=True, timestamps=timestamps)
    if not backup_source:
        # Signal error by returning a true value.
        return True
    if only_check:
        return
    if os.path.exists(destination):
        logger.info("Removing %s", destination)
        shutil.rmtree(destination)
    os.mkdir(destination)
    logger.info("Extracting %s to %s", backup_source, destination)
    if backup_source.endswith('gz'):
        tar_command = "tar xzf"
    else:
        tar_command = "tar xf"
    cmd = "%s %s -C %s" % (tar_command, backup_source, destination)
    logger.info(cmd)
    output, failed = utils.system(cmd)
    if output:
        print(output)
    if failed:
        return


def remove_orphaned_blob_backups(backup_location, fs_backup_location,
                                 archive=False):
    """Remove orphaned blob backups.

    This means: blob backups that have a timestamp older than the oldest
    filestorage backup.

    Returns True when nothing is left to do for any other code
    that might want to do cleanup.
    """
    if not fs_backup_location:
        return
    oldest_timestamp = get_oldest_filestorage_timestamp(fs_backup_location)
    if not oldest_timestamp:
        return
    logger.debug('Removing blob backups with timestamp before %s from %s',
                 oldest_timestamp, backup_location)
    if archive:
        backup_getter = get_blob_backup_archives
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
        logger.info("Removed %d blob backup(s), all backups "
                    "belonging to remaining filestorage backups have "
                    "been kept.", deleted)
    # We are done.
    return True


def cleanup(backup_location, full=False, keep=0, keep_blob_days=0,
            fs_backup_location=None):
    """Clean up old blob backups.

    When fs_backup_location is passed and we find filestorage backups there,
    we ignore the keep and keep_blob_days options.
    We remove any blob backups that are older than the oldest
    filestorage backup.

    For the test, we create a backup dir using buildout's test support methods:

      >>> backup_dir = 'back'
      >>> mkdir(backup_dir)

    And we'll make a function that creates a blob backup directory for
    us and that also sets the file modification dates to a meaningful
    time.

      >>> import time
      >>> import os
      >>> def add_backup(name, days=0):
      ...     global next_mod_time
      ...     mkdir(backup_dir, name)
      ...     write(backup_dir, name, 'dummyfile', 'dummycontents')
      ...     # Change modification time to 'days' days old.
      ...     mod_time = time.time() - (86400 * days)
      ...     os.utime(join(backup_dir, name), (mod_time, mod_time))

    Calling 'cleanup' without a keep arguments will just return without doing
    anything.

      >>> cleanup(backup_dir)

    Cleaning an empty directory won't do a thing.

      >>> cleanup(backup_dir, keep=1)
      >>> cleanup(backup_dir, keep_blob_days=1)

    Adding one backup file and cleaning the directory won't remove it either:

      >>> add_backup('blob.1', days=1)
      >>> cleanup(backup_dir, keep=1)
      >>> ls(backup_dir)
      d  blob.1

    When we add a second backup directory and we keep only one then
    this means the first one gets removed.

      >>> add_backup('blob.0', days=0)
      >>> cleanup(backup_dir, keep=1)
      >>> ls(backup_dir)
      d  blob.0

    Note that we do keep an eye on the name of the blob directories,
    as unless someone has been messing manually with the names and
    modification dates we only expect blob.0, blob.1, blob.2, etc, as
    names, with blob.0 being the most recent.

    Any files are ignored and any directories that do not match
    prefix.X get ignored:

      >>> add_backup('myblob')
      >>> add_backup('blob.some.3')
      >>> write(backup_dir, 'blob.4', 'just a file')
      >>> write(backup_dir, 'blob5.txt', 'just a file')
      >>> cleanup(backup_dir, keep=1)
      >>> ls(backup_dir)
      d  blob.0
      -  blob.4
      d  blob.some.3
      -  blob5.txt
      d  myblob

    We do not mind what the prefix is, as long as there is only one prefix:

      >>> add_backup('myblob.4')
      >>> cleanup(backup_dir, keep=1)
      Traceback (most recent call last):
      ...
      SystemExit: 1
      >>> cleanup(backup_dir, keep_blob_days=1)
      Traceback (most recent call last):
      ...
      SystemExit: 1
      >>> ls(backup_dir)
      d  blob.0
      -  blob.4
      d  blob.some.3
      -  blob5.txt
      d  myblob
      d  myblob.4

    We create a helper function that gives us a fresh directory with
    some blob backup directories, where backups are made twice a day:

      >>> def fresh_backups(num):
      ...     remove(backup_dir)
      ...     mkdir(backup_dir)
      ...     for b in range(num):
      ...         name = 'blob.%d' % b
      ...         add_backup(name, days=b / 2.0)

    We keep the last 4 backups:

      >>> fresh_backups(10)
      >>> cleanup(backup_dir, keep=4)
      >>> ls(backup_dir)
      d  blob.0
      d  blob.1
      d  blob.2
      d  blob.3
      >>> fresh_backups(10)

    We keep the last 4 days of backups:

      >>> cleanup(backup_dir, keep_blob_days=4)
      >>> ls(backup_dir)
      d  blob.0
      d  blob.1
      d  blob.2
      d  blob.3
      d  blob.4
      d  blob.5
      d  blob.6
      d  blob.7

    With full=False (the default) we ignore the keep option:

      >>> cleanup(backup_dir, full=False, keep=2, keep_blob_days=2)
      >>> ls(backup_dir)
      d  blob.0
      d  blob.1
      d  blob.2
      d  blob.3

    With full=True we ignore the keep_blob_days option:

      >>> cleanup(backup_dir, full=True, keep=2, keep_blob_days=2)
      >>> ls(backup_dir)
      d  blob.0
      d  blob.1

    Cleanup after the test.

      >>> remove(backup_dir)

    """
    logger.debug('Starting cleanup of blob backups from %s', backup_location)
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
    logger.debug("Trying to clean up old backups.")
    backup_dirs = get_blob_backup_dirs(backup_location)
    if full:
        logger.debug("This is a full backup.")
        logger.debug("Max number of backups: %d.", keep)
        logger.debug("Number of blob days to keep: %d (ignored).",
                     keep_blob_days)
    else:
        logger.debug("This is a partial backup.")
        logger.debug("Minimum number of backups to keep: %d.", keep)
        logger.debug("Number of blob days to keep: %d.", keep_blob_days)
    if len(backup_dirs) > keep and keep != 0:
        logger.debug("There are older backups that we can remove.")
        possibly_remove = backup_dirs[keep:]
        logger.debug("Will possibly remove: %r", possibly_remove)
        deleted = 0
        now = time.time()
        for num, mod_time, directory in possibly_remove:
            if keep_blob_days:
                mod_days = (now - mod_time) / 86400  # 24 * 60 * 60
                if mod_days < keep_blob_days:
                    # I'm too young to die!
                    continue
            shutil.rmtree(directory)
            deleted += 1
            logger.debug("Deleted %s.", directory)
        if deleted:
            if full:
                logger.info("Removed %d blob backup(s), the latest "
                            "%d backup(s) have been kept.", deleted, keep)
            else:
                logger.info("Removed %d blob backup(s), the latest "
                            "%d day(s) of backups have been kept.", deleted,
                            keep_blob_days)
    else:
        logger.debug("Not removing backups.")


def cleanup_archives(
    backup_location,
    keep=0,
    fs_backup_location=None
):
    """Clean up old blob backups.

    When fs_backup_location is passed and we find filestorage backups there,
    we ignore the keep and keep_blob_days options.
    We remove any blob backups that are older than the oldest
    filestorage backup.

    For the test, we create a backup dir using buildout's test support methods:

      >>> backup_dir = 'back'
      >>> mkdir(backup_dir)

    And we'll make a function that creates a blob backup directory for
    us and that also sets the file modification dates to a meaningful
    time.

      >>> import time
      >>> import os
      >>> def add_backup(name, days=0):
      ...     global next_mod_time
      ...     write(backup_dir, name, 'dummycontents')
      ...     # Change modification time to 'days' days old.
      ...     mod_time = time.time() - (86400 * days)
      ...     os.utime(join(backup_dir, name), (mod_time, mod_time))

    Calling 'cleanup_archives' without a keep arguments will just return without
    doing anything.

      >>> cleanup_archives(backup_dir)

    Cleaning an empty directory won't do a thing.

      >>> cleanup_archives(backup_dir, keep=1)

    Adding one backup file and cleaning the directory won't remove it either:

      >>> add_backup('blob.1.tar', days=1)
      >>> cleanup_archives(backup_dir, keep=1)
      >>> ls(backup_dir)
      -  blob.1.tar

    When we add a second backup directory and we keep only one then
    this means the first one gets removed.

      >>> add_backup('blob.0.tar.gz', days=0)
      >>> cleanup_archives(backup_dir, keep=1)
      >>> ls(backup_dir)
      -  blob.0.tar.gz

    Note that we do keep an eye on the name of the blob directories,
    as unless someone has been messing manually with the names and
    modification dates we only expect blob.0, blob.1, blob.2, etc, as
    names, with blob.0 being the most recent.

    Any files are ignored and any directories that do not match
    prefix.X get ignored:

      >>> add_backup('myblob.tar.gz')
      >>> add_backup('blob.some.3.tar')
      >>> mkdir(backup_dir, 'blob.4.tar')
      >>> write(backup_dir, 'blob5.txt', 'just a file')
      >>> cleanup_archives(backup_dir, keep=1)
      >>> ls(backup_dir)
      -  blob.0.tar.gz
      d  blob.4.tar
      -  blob.some.3.tar
      -  blob5.txt
      -  myblob.tar.gz

    We create a helper function that gives us a fresh directory with
    some blob backup directories, where backups are made twice a day:

      >>> def fresh_backups(num, compress=False):
      ...     remove(backup_dir)
      ...     mkdir(backup_dir)
      ...     for b in range(num):
      ...         name = 'blob.%d.tar' % b
      ...         if compress:
      ...             name += '.gz'
      ...         add_backup(name, days=b / 2.0)

    We keep the last 4 backups:

      >>> fresh_backups(10, compress=True)
      >>> cleanup_archives(backup_dir, keep=4)
      >>> ls(backup_dir)
      -  blob.0.tar.gz
      -  blob.1.tar.gz
      -  blob.2.tar.gz
      -  blob.3.tar.gz

      >>> fresh_backups(10)
      >>> cleanup_archives(backup_dir, keep=4)
      >>> ls(backup_dir)
      -  blob.0.tar
      -  blob.1.tar
      -  blob.2.tar
      -  blob.3.tar

    Cleanup after the test.

      >>> remove(backup_dir)

    """
    logger.debug('Starting cleanup of blob archives from %s', backup_location)
    if remove_orphaned_blob_backups(backup_location, fs_backup_location,
                                    archive=True):
        # A True return value means there is nothing left to do.
        return

    # Making sure we use integers.
    keep = int(keep)
    logger.debug("Trying to clean up old backups.")
    backup_archives = get_blob_backup_archives(backup_location)
    logger.debug("This is a full backup.")
    logger.debug("Max number of backups: %d.", keep)
    if len(backup_archives) > keep and keep != 0:
        logger.debug("There are older backups that we can remove.")
        possibly_remove = backup_archives[keep:]
        logger.debug("Will possibly remove: %r", possibly_remove)
        deleted = 0
        for num, mod_time, archive_file in possibly_remove:
            os.remove(archive_file)
            deleted += 1
            logger.debug("Deleted %s.", archive_file)
        if deleted:
            logger.info("Removed %d blob backup(s), the latest "
                        "%d backup(s) have been kept.", deleted, keep)
    else:
        logger.debug("Not removing backups.")
