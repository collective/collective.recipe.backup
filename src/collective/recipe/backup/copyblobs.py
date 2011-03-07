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


# Find directories blobstorage.0, blobstorage.1, etc:
previous_backups = [d for d in os.listdir(BACKUP_DIR)
                    if d.startswith(SOURCE + '.')]
sorted_backups = sorted(previous_backups, cmp=strict_cmp_backups, reverse=True)

# Rotate the directories.
for directory in sorted_backups:
    new_num = int(directory.split('.')[-1]) + 1
    new_name = '%s.%s' % (SOURCE, new_num)
    print "Renaming %s to %s." % (directory, new_name)
    os.rename(os.path.join(BACKUP_DIR, directory),
              os.path.join(BACKUP_DIR, new_name))

prev_link = os.path.join('..', SOURCE + '.1')
prev = os.path.join(BACKUP_DIR, SOURCE + '.1')
dest = os.path.join(BACKUP_DIR, SOURCE + '.0')
if os.path.isdir(prev):
    # Hardlink against the previous directory.  Done by hand it would be:
    # rsync -a --delete --link-dest=../blobstorage.1 blobstorage/
    #    backups/blobstorage.0/
    cmd = 'rsync -a --delete --link-dest=%(link)s %(source)s %(dest)s' % dict(
        link=prev_link,
        source=SOURCE,
        dest=dest)
else:
    # No previous directory to hardlink against.
    cmd = 'rsync -a %(source)s %(dest)s' % dict(
        source=SOURCE,
        dest=dest)
print cmd
# XXX Get output in a different way, or at least errors.
print os.system(cmd)
