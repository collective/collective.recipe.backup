"""
NOTE: THIS IS A HACK!

Or rather, this is work in progress that is completely not hooked up
to anything yet, but that is the start of something that seems to work
when you copy it to your buildout/var directory and run it directly
from there.

Experiment with this at your own risk.

The idea is to use rsync and hard links; this probably requires a
unixy (Linux, Mac OS X) operating system.

It is based on this article by Mike Rubel:
http://www.mikerubel.org/computers/rsync_snapshots/

"""

import os
import logging
#import shutil
logger = logging.getLogger('blobs')

from collective.recipe.backup import utils

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
    >>> get_valid_directories('dirtest', 'a')
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


def backup_blobs(source, destination, full=False):
    """Copy blobs from source to destination.

    Source is usually something like var/blobstorage and destination
    would be var/blobstoragebackups.  Within that destination we
    create a subdirectory with a fresh blob backup from the source.

    We can make a full backup or a partial backup.  Partial backups
    are done with rsync and hard links to safe disk space.  Actually,
    full backups used to avoid the hard links, but that did not really
    have any extra value, so now it does the same thing, just in its
    own directory.

    Note that we end up with something like var/blobstorage copied to
    var/blobbackups/blobstorage.0/blobstorage.  We could copy the
    contents of var/blobstorage directly to blobstorage.0, but then
    the disk space safing hard links do not work.

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
    rotate_directories(destination, base_name)

    prev = os.path.join(destination, base_name + '.1')
    dest = os.path.join(destination, base_name + '.0')
    if os.path.exists(prev):
        # Make a 'partial' backup by reusing the previous backup.  We
        # might not want to do this for full backups, but this is a
        # lot faster and the end result really is the same, so why
        # not.
        if not os.path.isdir(prev):
            # Should have been caught already.
            raise Exception("%s must be a directory" % prev)
        # Hardlink against the previous directory.  Done by hand it would be:
        # rsync -a --delete --link-dest=../blobstorage.1 blobstorage/
        #     backups/blobstorage.0
        prev_link = os.path.join(os.pardir, base_name + '.1')
        cmd = 'rsync -a --delete --link-dest=%(link)s %(source)s %(dest)s' % \
              dict(link=prev_link,
                   source=source,
                   dest=dest)
    else:
        # No previous directory to hardlink against.
        cmd = 'rsync -a %(source)s %(dest)s' % dict(
            source=source,
            dest=dest)
    logger.info(cmd)
    output = utils.system(cmd)
    if output:
        # If we have output, this means there was an error.
        logger.error(output)


def restore_blobs(source, destination):
    """Restore blobs from source to destination.

    We could remove the destination first (with
    'shutil.rmtree(destination)'), but an 'rsync -a --delete' works
    faster.

    Note that trailing slashes in source and destination do matter, so
    be careful with that otherwise you may end up with something like
    var/blobstorage/blobstorage
    """
    if destination.endswith(os.sep):
        # strip that separator
        destination = destination[:-len(os.sep)]
    base_name = os.path.basename(destination)
    dest_dir = os.path.dirname(destination)
    last_source = os.path.join(source, base_name + '.0', base_name)
    # You should end up with something like this:
    #rsync -a --delete var/blobstoragebackups/blobstorage.0/blobstorage var/
    cmd = 'rsync -a --delete %(source)s %(dest)s' % dict(
        source=last_source,
        dest=dest_dir)
    logger.info(cmd)
    output = utils.system(cmd)
    if output:
        # If we have output, this means there was an error.
        logger.error(output)
