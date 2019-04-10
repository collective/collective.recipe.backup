# -*-doctest-*-

Test the copyblobs.backup_blobs function
========================================

This especially tests backing up to directories.
For archives the function calls backup_blobs_archive, which has its own tests.

Import stuff.

    >>> from collective.recipe.backup.copyblobs import backup_blobs
    >>> from collective.recipe.backup.copyblobs import restore_blobs
    >>> import os
    >>> import time

Prepare some blobs.

    >>> mkdir('blobs')
    >>> write('blobs', 'one.txt', 'File One')
    >>> write('blobs', 'two.txt', 'File Two')
    >>> write('blobs', 'three.txt', 'File Three')
    >>> mkdir('blobs', 'dir')
    >>> mkdir('backups')

Do a backup.

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

    >>> write('blobs', 'one.txt', 'Changed File One')
    >>> write('blobs', 'four.txt', 'File Four')
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
    >>> backup0 = sorted(os.listdir('backups'))[0]
    >>> timestamp0 = backup0[len('blobs.'):]
    >>> ls('backups', backup0, 'blobs')
    d  dir
    -  four.txt
    -  one.txt
    -  three.txt

Wait a while, so we get a different timestamp, and then change some stuff.

    >>> time.sleep(1)
    >>> remove('blobs', 'three.txt')
    >>> remove('blobs', 'four.txt')
    >>> backup_blobs('blobs', 'backups', timestamps=True)
    >>> ls('backups')
    d  blobs.20...-...-...-...-...
    d  blobs.20...-...-...-...-...
    d  latest
    >>> print(os.path.realpath('backups/latest'))
    /sample-buildout/backups/blobs.20...-...-...-...-...
    >>> backup1 = sorted(os.listdir('backups'))[1]
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
    d  latest
    >>> len(sorted(os.listdir('backups')))  # The dots could shadow other backups.
    2
    >>> backup1 == sorted(os.listdir('backups'))[0]
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
    d  latest
    >>> len(sorted(os.listdir('backups')))  # The dots could shadow a third backup
    3
    >>> print(os.path.realpath('backups/latest'))
    /sample-buildout/backups/blobs.2100-01-01-00-00-00
    >>> ls('backups', 'blobs.2100-01-01-00-00-00', 'blobs')
    d  dir
    -  one.txt
    -  two.txt

Check a restore with archive=True.
This should prefer archives, but should be able to restore non-archives too.

    >>> ls('blobs')
    d  dir
    -  one.txt
    -  two.txt
    >>> restore_blobs('backups', os.path.abspath('blobs'), date='2099-01-01-00-00-00', archive_blob=True, timestamps=True)
    >>> ls('blobs')
    d  dir
    -  one.txt

Remove the oldest filestorage backup.

    >>> remove('fs', '{0}.fsz'.format(timestamp1))
    >>> backup_blobs('blobs', 'backups', timestamps=True,
    ...    fs_backup_location='fs')
    >>> ls('backups')
    d  blobs.2100-01-01-00-00-00
    d  latest
    >>> len(sorted(os.listdir('backups')))
    2
    >>> print(os.path.realpath('backups/latest'))
    /sample-buildout/backups/blobs.2100-01-01-00-00-00

Cleanup:

    >>> remove('blobs')
    >>> remove('backups')

We do mostly the same as above, but now using full backups.

    >>> mkdir('blobs')
    >>> write('blobs', 'one.txt', 'File One')
    >>> write('blobs', 'two.txt', 'File Two')
    >>> write('blobs', 'three.txt', 'File Three')
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

    >>> write('blobs', 'one.txt', 'Changed File One')
    >>> write('blobs', 'four.txt', 'File Four')
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
