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


def strict_cmp_backups(a, b):
    """Compare backups.

    a and b MUST be something like blobstorage.0 and
    blobstorage.1, which should be sorted numerically.

    >>> strict_cmp_backups('foo.0', 'foo.1')
    -1
    >>> strict_cmp_backups('foo.0', 'foo.0')
    0
    >>> strict_cmp_backups('foo.1', 'foo.0')
    1
    >>> strict_cmp_backups('foo.9', 'foo.10')
    -1
    >>> strict_cmp_backups('foo.1', 'bar.1')
    Traceback (most recent call last):
    ...
    ValueError: Not the same start for directories: 'foo.1' vs 'bar.1'

    """
    a_start, a_num = a.rsplit('.', 1)
    b_start, b_num = b.rsplit('.', 1)
    if a_start != b_start:
        raise ValueError(
            "Not the same start for directories: %r vs %r" % (a, b))
    a_num = int(a_num)
    b_num = int(b_num)
    return cmp(a_num, b_num)


def strict_cmp_gzips(a, b):
    """Compare backups.

    a and b MUST be something like blobstorage.0.tar.gz and
    blobstorage.1.tar.gz, which should be sorted numerically.

    >>> strict_cmp_gzips('foo.0.tar.gz', 'foo.1.tar.gz')
    -1
    >>> strict_cmp_gzips('foo.0.tar.gz', 'foo.0.tar.gz')
    0
    >>> strict_cmp_gzips('foo.1.tar.gz', 'foo.0.tar.gz')
    1
    >>> strict_cmp_gzips('foo.9.tar.gz', 'foo.10.tar.gz')
    -1
    >>> strict_cmp_gzips('foo.1.tar.gz', 'bar.1.tar.gz')
    Traceback (most recent call last):
    ...
    ValueError: Not the same start for files: 'foo.1.tar.gz' vs 'bar.1.tar.gz'

    """

    a_match = re.match("^(.+)\.(\d+)\.tar\.gz$", a)
    b_match = re.match("^(.+)\.(\d+)\.tar\.gz$", b)

    if a_match is None:
        raise ValueError("No match: %r" % a)

    if b_match is None:
        raise ValueError("No match: %r" % b)

    a_start, a_num = a_match.groups()
    b_start, b_num = b_match.groups()
    if a_start != b_start:
        raise ValueError(
            "Not the same start for files: %r vs %r" % (a, b)
        )
    a_num = int(a_num)
    b_num = int(b_num)
    return cmp(a_num, b_num)


def get_valid_directories(container, name):
    """Get subdirectories in container that start with 'name'.

    Subdirectories are expected to be something like blobstorage.0,
    blobstorage.1, etc.  We refuse to work when an accepted name is
    not actually a directory as this will mess up our logic further
    on.  No one should manually add files or directories here.

    Using the zc.buildout tools we create some directories and files:

    >>> mkdir('dirtest')
    >>> get_valid_directories('dirtest', 'a')
    []
    >>> for d in ['a', 'a.0', 'a.1', 'a.bar.2', 'a.bar']:
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


def get_valid_gzips(container, name):
    """Get gzip files in container that start with 'name'.

    Gzip files are expected to be something like blobstorage.0.tar.gz,
    blobstorage.1.tar.gz, etc.  We refuse to work when an accepted name is
    not actually a file as this will mess up our logic further
    on.  No one should manually add files or directories here.

    Using the zc.buildout tools we create some directories and files:

    >>> mkdir('dirtest')
    >>> get_valid_gzips('dirtest', 'a.tar.gz')
    []
    >>> for gz in ['a.tar.gz', 'a.0.tar.gz', 'a.1.tar.gz', 'a.bar.2.tar.gz']:
    ...     write('dirtest', gz, "Test file.")
    >>> sorted(get_valid_gzips('dirtest', 'a'))
    ['a.0.tar.gz', 'a.1.tar.gz']
    >>> get_valid_gzips('dirtest', 'bar')
    []

    We break when encountering a correct name that is a directory where we
    expect a file.

    >>> mkdir('dirtest', 'a.3.tar.gz')
    >>> get_valid_gzips('dirtest', 'a')
    Traceback (most recent call last):
    ...
    Exception: Refusing to rotate a.3.tar.gz as it is not a file.
    >>> get_valid_gzips('dirtest', 'bar')
    []

    Cleanup:

    >>> remove('dirtest')
    """
    valid_entries = []
    for entry in os.listdir(container):
        matched = re.match("^%s\.(\d+)\.tar\.gz$" % name, entry)
        if matched is None:
            continue
        if not os.path.isfile(os.path.join(container, entry)):
            raise Exception("Refusing to rotate %s as it is not a file." %
                            entry)
        valid_entries.append(entry)
    return valid_entries


def rotate_directories(container, name):
    """Rotate subdirectories in container that start with 'name'.

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


def rotate_gzips(container, name):
    """Rotate gzip files in container that start with 'name'.

    Using the zc.buildout tools we create some directories and files:

    >>> mkdir('dirtest')
    >>> rotate_gzips('dirtest', 'a')
    >>> for gz in ['a.0.tar.gz', 'a.1.tar.gz', 'a.2.tar.gz', 'a.9.tar.gz']:
    ...     write('dirtest', gz, "File content.")
    >>> ls('dirtest')
    -  a.0.tar.gz
    -  a.1.tar.gz
    -  a.2.tar.gz
    -  a.9.tar.gz
    >>> rotate_gzips('dirtest', 'a')
    >>> ls('dirtest')
    -  a.1.tar.gz
    -  a.10.tar.gz
    -  a.2.tar.gz
    -  a.3.tar.gz
    >>> rotate_gzips('dirtest', 'a')
    >>> ls('dirtest')
    -  a.11.tar.gz
    -  a.2.tar.gz
    -  a.3.tar.gz
    -  a.4.tar.gz

    Cleanup:

    >>> remove('dirtest')

    """
    previous_backups = get_valid_gzips(container, name)
    sorted_backups = sorted(previous_backups, cmp=strict_cmp_gzips,
                            reverse=True)
    # Rotate the directories.
    for entry in sorted_backups:
        matched = re.match("^%s\.(\d+)\.tar\.gz$" % name, entry)
        new_num = int(matched.groups()[0]) + 1
        new_name = "%s.%s.tar.gz" % (name, new_num)
        logger.info("Renaming %s to %s.", entry, new_name)
        os.rename(os.path.join(container, entry),
                  os.path.join(container, new_name))


def get_blob_backup_dirs(backup_location):
    """Get blob backup dirs from this location.
    """
    filenames = os.listdir(backup_location)
    logger.debug("Looked up filenames in the target dir: %s found. %r.",
                 len(filenames), filenames)
    backup_dirs = []
    prefix = ''
    for filename in filenames:
        # We only want directories of the form prefix.X, where X is an
        # integer.  There should not be anything else, but we like to
        # be safe.
        full_path = os.path.join(backup_location, filename)
        if not os.path.isdir(full_path):
            continue
        if filename in (os.curdir, os.pardir):
            # These should not be listed by os.listdir, but again: we
            # like to be safe.
            continue
        parts = filename.split('.')
        if len(parts) != 2:
            continue
        try:
            num = int(parts[1])
        except:
            # No number
            continue
        if prefix:
            if parts[0] != prefix:
                logger.error(
                    "Different backup prefixes found in %s (%s, %s). Are you "
                    "mixing two backups in one directory? For safety we will "
                    "not cleanup old backups here." % (
                        backup_location, prefix, parts[0]))
                sys.exit(1)
        else:
            prefix = parts[0]
        mod_time = os.path.getmtime(full_path)
        backup_dirs.append((num, mod_time, full_path))
    # We always sort by backup number:
    backup_dirs = sorted(backup_dirs, key=itemgetter(0))
    # Check if this is the same as reverse sorting by modification time:
    mod_times = sorted(backup_dirs, key=itemgetter(1), reverse=True)
    if backup_dirs != mod_times:
        logger.warn("Sorting blob backups by number gives other result than "
                    "reverse sorting by last modification time.")
    logger.debug("Found %d blob backups: %r.", len(backup_dirs),
                 [d[1] for d in backup_dirs])
    return backup_dirs


def get_blob_backup_gzips(backup_location):
    """Get blob backup gzip files from this location.
    """
    filenames = os.listdir(backup_location)
    logger.debug("Looked up filenames in the target dir: %s found. %r.",
                 len(filenames), filenames)
    backup_gzips = []
    for filename in filenames:
        # We only want directories of the form prefix.X.tar.gz, where X is an
        # integer. There should not be anything else, but we like to
        # be safe.
        full_path = os.path.join(backup_location, filename)
        if not os.path.isfile(full_path):
            continue

        matched = re.match("^([^\.]+)\.(\d+)\.tar\.gz$", filename)

        if matched is None:
            continue

        num = int(matched.groups()[1])

        mod_time = os.path.getmtime(full_path)

        backup_gzips.append((num, mod_time, full_path))

    # We always sort by backup number:
    backup_gzips = sorted(backup_gzips, key=itemgetter(0))

    # Check if this is the same as reverse sorting by modification time:
    mod_times = sorted(backup_gzips, key=itemgetter(1), reverse=True)

    if backup_gzips != mod_times:
        logger.warn("Sorting blob backups by number gives other result than "
                    "reverse sorting by last modification time.")
    logger.debug("Found %d blob backups: %r.", len(backup_gzips),
                 [d[1] for d in backup_gzips])
    return backup_gzips


def backup_blobs(source, destination, full=False, use_rsync=True,
                 keep=0, keep_blob_days=0, gzip_blob=False, rsync_options=''):
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
    >>> backup_blobs('blobs', 'backups')
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

    Cleanup:

    >>> remove('blobs')
    >>> remove('backups')

    We do exactly the same (if developers remember to copy changes
    done above to below) but now using full backups.

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

    Cleanup:

    >>> remove('blobs')
    >>> remove('backups')

    """
    base_name = os.path.basename(source)

    if gzip_blob:
        backup_blobs_gzip(source, destination, keep)
        return

    rotate_directories(destination, base_name)

    prev = os.path.join(destination, base_name + '.1')
    dest = os.path.join(destination, base_name + '.0')
    if use_rsync:
        if os.path.exists(prev):
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
            prev_link = os.path.join(os.pardir, base_name + '.1')
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
    cleanup(destination, full, keep, keep_blob_days)


def backup_blobs_gzip(source, destination, keep=0):
    """Make gzip archive from blobs in source directory.

    Source is usually something like var/blobstorage and destination
    would be var/blobstoragebackups.  Within that destination we
    create a gzip file with a fresh blob backup from the source.

    We use 'keep' to simply keep the last X backups.

    Again, let's test this using the tools from zc.buildout:

    >>> mkdir('blobs')
    >>> write('blobs', 'one.txt', "File One")
    >>> write('blobs', 'two.txt', "File Two")
    >>> write('blobs', 'three.txt', "File Three")
    >>> mkdir('blobs', 'dir')
    >>> mkdir('backups')
    >>> backup_blobs_gzip('blobs', 'backups', keep=0)
    >>> ls('backups')
    -  blobs.0.tar.gz

    Change some stuff.

    >>> write('blobs', 'one.txt', "Changed File One")
    >>> write('blobs', 'four.txt', "File Four")
    >>> remove('blobs', 'two.txt')
    >>> backup_blobs_gzip('blobs', 'backups')
    >>> ls('backups')
    -  blobs.0.tar.gz
    -  blobs.1.tar.gz

    Cleanup:

    >>> remove('blobs')
    >>> remove('backups')
    """
    base_name = os.path.basename(source)
    if not os.path.exists(destination):
        os.makedirs(destination)
    rotate_gzips(destination, base_name)
    dest = os.path.join(destination, base_name + '.0.tar.gz')
    if os.path.exists(dest):
        raise Exception("Path already exists: %s" % dest)
    cmd = "tar czf %s -C %s ." % (dest, source)
    logger.info(cmd)
    output, failed = utils.system(cmd)
    if output:
        print(output)
    if failed:
        return
    # Now possibly remove old backups.
    cleanup_gzips(destination, keep=keep)


def restore_blobs(source, destination, use_rsync=True,
                  date=None, gzip_blob=False, rsync_options=''):
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
    """

    if gzip_blob:
        restore_blobs_gzip(source, destination, date)
        return

    if destination.endswith(os.sep):
        # strip that separator
        destination = destination[:-len(os.sep)]
    base_name = os.path.basename(destination)
    dest_dir = os.path.dirname(destination)

    # Determine the source (blob backup) that should be restored.
    backup_source = None
    if date is not None:
        # From repozo: specify UTC (not local) time in this format:
        # yyyy-mm-dd[-hh[-mm[-ss]]]
        # Note that this matches the 2011-10-05-12-12-45.fsz that is created.
        try:
            date_args = [int(num) for num in date.split('-')]
        except:
            logger.info("Could not parse date argument to restore blobs: %r",
                        date)
            logger.info("Restoring most recent backup instead.")
        else:
            target_datetime = datetime(*date_args)
            backup_dirs = get_blob_backup_dirs(source)
            # We want to find the first backup after the requested
            # modification time, so we reverse the order.
            backup_dirs.reverse()  # Note: this reverses in place.
            for num, mod_time, directory in backup_dirs:
                backup_time = datetime.utcfromtimestamp(mod_time)
                if backup_time >= target_datetime:
                    backup_source = os.path.join(directory, base_name)
                    break
            if not backup_source:
                logger.warn("Could not find backup more recent than %r. Using "
                            "most recent instead.", date)

    if not backup_source:
        # The most recent is the default:
        backup_source = os.path.join(source, base_name + '.0', base_name)

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


def restore_blobs_gzip(source, destination, date=None):
    """Restore blobs from source to destination.

    Prepare backup for test:

    >>> mkdir('blobs')
    >>> write('blobs', 'one.txt', "File One")
    >>> write('blobs', 'two.txt', "File Two")
    >>> write('blobs', 'three.txt', "File Three")
    >>> mkdir('blobs', 'dir')
    >>> mkdir('backups')
    >>> backup_blobs_gzip('blobs', 'backups', keep=0)
    >>> ls('backups')
    -  blobs.0.tar.gz


    Test restore:

    >>> remove('blobs')
    >>> restore_blobs_gzip('backups', 'blobs')
    >>> ls('blobs')
    d  dir
    -  one.txt
    -  three.txt
    -  two.txt


    Cleanup:

    >>> remove('blobs')
    >>> remove('backups')
    """
    if destination.endswith(os.sep):
        # strip that separator
        destination = destination[:-len(os.sep)]
    base_name = os.path.basename(destination)

    # Determine the source (blob backup) that should be restored.
    backup_source = None
    if date is not None:
        # From repozo: specify UTC (not local) time in this format:
        # yyyy-mm-dd[-hh[-mm[-ss]]]
        # Note that this matches the 2011-10-05-12-12-45.fsz that is created.
        try:
            date_args = [int(num) for num in date.split('-')]
        except:
            logger.info("Could not parse date argument to restore blobs: %r",
                        date)
            logger.info("Restoring most recent backup instead.")
        else:
            target_datetime = datetime(*date_args)
            backup_gzips = get_blob_backup_gzips(source)
            # We want to find the first backup after the requested
            # modification time, so we reverse the order.
            backup_gzips.reverse()  # Note: this reverses in place.
            for num, mod_time, gzip_file in backup_gzips:
                backup_time = datetime.utcfromtimestamp(mod_time)
                if backup_time >= target_datetime:
                    backup_source = gzip_file
                    break
            if not backup_source:
                logger.warn("Could not find backup more recent than %r. Using "
                            "most recent instead.", date)

    if not backup_source:
        # The most recent is the default:
        backup_source = os.path.join(
            source, base_name + '.0.tar.gz'
        )

    if os.path.exists(destination):
        logger.info("Removing %s", destination)
        shutil.rmtree(destination)
    os.mkdir(destination)
    logger.info("Extracting %s to %s", backup_source, destination)
    cmd = "tar xzf %s -C %s" % (backup_source, destination)
    logger.info(cmd)
    output, failed = utils.system(cmd)
    if output:
        print(output)
    if failed:
        return


def cleanup(backup_location, full=False, keep=0, keep_blob_days=0):
    """Clean up old blob backups.

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


def cleanup_gzips(backup_location, keep=0):
    """Clean up old blob backups.

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

    Calling 'cleanup_gzips' without a keep arguments will just return without
    doing anything.

      >>> cleanup_gzips(backup_dir)

    Cleaning an empty directory won't do a thing.

      >>> cleanup_gzips(backup_dir, keep=1)

    Adding one backup file and cleaning the directory won't remove it either:

      >>> add_backup('blob.1.tar.gz', days=1)
      >>> cleanup_gzips(backup_dir, keep=1)
      >>> ls(backup_dir)
      -  blob.1.tar.gz

    When we add a second backup directory and we keep only one then
    this means the first one gets removed.

      >>> add_backup('blob.0.tar.gz', days=0)
      >>> cleanup_gzips(backup_dir, keep=1)
      >>> ls(backup_dir)
      -  blob.0.tar.gz

    Note that we do keep an eye on the name of the blob directories,
    as unless someone has been messing manually with the names and
    modification dates we only expect blob.0, blob.1, blob.2, etc, as
    names, with blob.0 being the most recent.

    Any files are ignored and any directories that do not match
    prefix.X get ignored:

      >>> add_backup('myblob.tar.gz')
      >>> add_backup('blob.some.3.tar.gz')
      >>> mkdir(backup_dir, 'blob.4.tar.gz')
      >>> write(backup_dir, 'blob5.txt', 'just a file')
      >>> cleanup_gzips(backup_dir, keep=1)
      >>> ls(backup_dir)
      -  blob.0.tar.gz
      d  blob.4.tar.gz
      -  blob.some.3.tar.gz
      -  blob5.txt
      -  myblob.tar.gz

    We create a helper function that gives us a fresh directory with
    some blob backup directories, where backups are made twice a day:

      >>> def fresh_backups(num):
      ...     remove(backup_dir)
      ...     mkdir(backup_dir)
      ...     for b in range(num):
      ...         name = 'blob.%d.tar.gz' % b
      ...         add_backup(name, days=b / 2.0)

    We keep the last 4 backups:

      >>> fresh_backups(10)
      >>> cleanup_gzips(backup_dir, keep=4)
      >>> ls(backup_dir)
      -  blob.0.tar.gz
      -  blob.1.tar.gz
      -  blob.2.tar.gz
      -  blob.3.tar.gz

    Cleanup after the test.

      >>> remove(backup_dir)

    """
    # Making sure we use integers.
    keep = int(keep)
    logger.debug("Trying to clean up old backups.")
    backup_gzips = get_blob_backup_gzips(backup_location)
    logger.debug("This is a full backup.")
    logger.debug("Max number of backups: %d.", keep)
    if len(backup_gzips) > keep and keep != 0:
        logger.debug("There are older backups that we can remove.")
        possibly_remove = backup_gzips[keep:]
        logger.debug("Will possibly remove: %r", possibly_remove)
        deleted = 0
        for num, mod_time, gzip_file in possibly_remove:
            os.remove(gzip_file)
            deleted += 1
            logger.debug("Deleted %s.", gzip_file)
        if deleted:
            logger.info("Removed %d blob backup(s), the latest "
                        "%d backup(s) have been kept.", deleted, keep)
    else:
        logger.debug("Not removing backups.")
