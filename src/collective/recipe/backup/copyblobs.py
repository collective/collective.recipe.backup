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
logger = logging.getLogger('backup')

SOURCE = 'blobstorage'
BACKUP_DIR = 'backups'


def strict_cmp_backups(a, b):
    """Compare backups.

    a and b MUST be something like blobstorage.0 and
    blobstorage.1, which should be sorted numerically.
    """
    a_start, a_num = a.rsplit('.', 1)
    b_start, b_num = b.rsplit('.', 1)
    if a_start != b_start:
        raise Exception('Not the same start for directories: %r vs %r', a, b)
    a_num = int(a_num)
    b_num = int(b_num)
    return cmp(a_num, b_num)


def get_valid_directories(container, name):
    """Get subdirectories in container that start with 'name'.

    Subdirectories are expected to be something like blobstorage.0,
    blobstorage.1, etc.  We refuse to work when an accepted name is
    not actually a directory as this will mess up our logic further
    on.  No one should manually add files or directories here.
    """
    valid_entries = []
    for entry in os.listdir(container):
        if not entry.startswith(name + '.'):
            continue
        try:
            entry_start, entry_num = entry.rsplit('.', 1)
        except ValueError:
            # This is not the entry we are looking for.
            continue
        if entry_start != name:
            # Maybe something like 'blobstorage.break.me.0'
            logger.warn("Ignoring entry %s in %s", entry, container)
            continue
        try:
            entry_num = int(entry_num)
        except (ValueError, TypeError):
            continue
        # Looks like we have a winner.  It must be a directory though.
        if not os.path.isdir(entry):
            raise Exception("Refusing to rotate %s as it is not a directory." %
                            entry)
        valid_entries.append(entry)
    return valid_entries


def rotate_directories(container, name):
    """Rotate subdirectories in container that start with 'name'.
    """
    previous_backups = get_valid_directories(container, name)
    sorted_backups = sorted(previous_backups, cmp=strict_cmp_backups,
                            reverse=True)
    # Rotate the directories.
    for directory in sorted_backups:
        new_num = int(directory.split('.')[-1]) + 1
        new_name = '%s.%s' % (name, new_num)
        logger.info("Renaming %s to %s.", directory, new_name)
        os.rename(os.path.join(container_DIR, directory),
                  os.path.join(container, new_name))


def backup_blobs(source, destination, full):
    """Copy blobs from source to destination.

    Source is usually something like var/blobstorage and destination
    would be var/blobstoragebackups.  Within that destination we
    create a subdirectory with a fresh blob backup from the source.

    We can make a full backup or a partial backup.  Partial backups
    are done with rsync and hard links to safe disk space.  Full
    backups only use rsync (we might want to simply copy in this
    case).
    """
    base_name = os.path.basename(source)
    rotate_directories(destination, base_name)

    prev = os.path.join(destination, base_name + '.1')
    dest = os.path.join(destination, base_name + '.0')
    if (not full) and os.path.exists(prev):
        # Make a 'partial' backup by reusing the previous backup.
        if not os.path.isdir(prev):
            # Should have been caught already.
            raise Exception("%s must be a directory" % prev)
        # Hardlink against the previous directory.  Done by hand it would be:
        # rsync -a --delete --link-dest=../blobstorage.1 blobstorage/
        #    backups/blobstorage.0/
        prev_link = os.path.join(os.pardir, base_name + '.1')
        cmd = 'rsync -a --delete --link-dest=%(link)s %(source)s %(dest)s' % dict(
            link=prev_link,
            source=source,
            dest=dest)
    else:
        # No previous directory to hardlink against.
        cmd = 'rsync -a %(source)s %(dest)s' % dict(
            source=source,
            dest=dest)
    logger.info(cmd)
    # XXX Get output in a different way, or at least errors.
    output = os.system(cmd)
    logger.info(output)
