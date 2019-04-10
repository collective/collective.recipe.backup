# -*-doctest-*-

Test the copyblobs.backup_blobs_archive function
================================================

Import stuff.

    >>> from collective.recipe.backup.copyblobs import backup_blobs_archive
    >>> from collective.recipe.backup.copyblobs import restore_blobs_archive
    >>> import time

Prepare some blobs.

    >>> mkdir('blobs')
    >>> write('blobs', 'one.txt', 'File One')
    >>> write('blobs', 'two.txt', 'File Two')
    >>> write('blobs', 'three.txt', 'File Three')
    >>> mkdir('blobs', 'dir')
    >>> mkdir('backups')
    >>> backup_blobs_archive('blobs', 'backups', keep=0)
    >>> ls('backups')
    -  blobs.0.tar

Change some stuff and compress.

    >>> write('blobs', 'one.txt', 'Changed File One')
    >>> write('blobs', 'four.txt', 'File Four')
    >>> remove('blobs', 'two.txt')
    >>> backup_blobs_archive('blobs/', 'backups', compress_blob=True)
    >>> ls('backups')
    -  blobs.0.tar.gz
    -  blobs.1.tar

Change some stuff and no longer compress.

    >>> write('blobs', 'one.txt', 'Changed File One Again')
    >>> backup_blobs_archive('blobs', 'backups')
    >>> ls('backups')
    -  blobs.0.tar
    -  blobs.1.tar.gz
    -  blobs.2.tar

Use timestamps with a fs_backup_location.

    >>> mkdir('fs')
    >>> write('fs', '2017-05-24-11-54-39.fsz', 'Dummy fs backup 24')
    >>> backup_blobs_archive(
    ...     'blobs', 'backups', fs_backup_location='fs', timestamps=True,
    ...     compress_blob=True)
    >>> ls('backups')
    -  blobs.0.tar
    -  blobs.1.tar.gz
    -  blobs.2.tar
    -  blobs.2017-05-24-11-54-39.tar.gz
    l  latest
    >>> import os
    >>> print(os.path.realpath('backups/latest'))
    /sample-buildout/backups/blobs.2017-05-24-11-54-39.tar.gz

And again with the same settings, as I saw something go wrong once.

    >>> backup_blobs_archive(
    ...     'blobs', 'backups', fs_backup_location='fs', timestamps=True,
    ...     compress_blob=True)
    >>> ls('backups')
    -  blobs.0.tar
    -  blobs.1.tar.gz
    -  blobs.2.tar
    -  blobs.2017-05-24-11-54-39.tar.gz
    l  latest

Same without compressing, which accepts previous compressed tarballs too.

    >>> backup_blobs_archive(
    ...     'blobs', 'backups', fs_backup_location='fs', timestamps=True,
    ...     compress_blob=False)
    >>> ls('backups')
    -  blobs.0.tar
    -  blobs.1.tar.gz
    -  blobs.2.tar
    -  blobs.2017-05-24-11-54-39.tar.gz
    l  latest

Same settings, now with a change and a newer filestorage backup.

    >>> write('fs', '2017-05-25-12-00-00.fsz', 'Full fs backup 25')
    >>> backup_blobs_archive(
    ...     'blobs', 'backups', fs_backup_location='fs', timestamps=True,
    ...     compress_blob=False)
    >>> ls('backups')
    -  blobs.0.tar
    -  blobs.1.tar.gz
    -  blobs.2.tar
    -  blobs.2017-05-24-11-54-39.tar.gz
    -  blobs.2017-05-25-12-00-00.tar
    l  latest
    >>> print(os.path.realpath('backups/latest'))
    /sample-buildout/backups/blobs.2017-05-25-12-00-00.tar

Now with incremental_blobs, which requires timestamps to be True.

    >>> backup_blobs_archive(
    ...     'blobs', 'backups', fs_backup_location='fs', timestamps=False,
    ...     compress_blob=False, incremental_blobs=True)
    Traceback (most recent call last):
    ...
    Exception: Cannot have incremental_blobs without timestamps.
    >>> backup_blobs_archive(
    ...     'blobs', 'backups', fs_backup_location='fs', timestamps=True,
    ...     compress_blob=False, incremental_blobs=True)
    >>> ls('backups')
    -  blobs.0.tar
    -  blobs.1.tar.gz
    -  blobs.2.tar
    -  blobs.2017-05-24-11-54-39.tar.gz
    -  blobs.2017-05-25-12-00-00.tar

Same settings, now with a newer filestorage delta backup.
This does not create a snapshot file yet, because
that is only done for a full backup.

    >>> write('blobs', 'one.txt', '25.1')
    >>> write('fs', '2017-05-25-13-00-00.deltafsz', 'Delta fs backup 25.1')
    >>> backup_blobs_archive(
    ...     'blobs', 'backups', fs_backup_location='fs', timestamps=True,
    ...     compress_blob=False, incremental_blobs=True)
    >>> ls('backups')
    -  blobs.0.tar
    -  blobs.1.tar.gz
    -  blobs.2.tar
    -  blobs.2017-05-24-11-54-39.tar.gz
    -  blobs.2017-05-25-12-00-00.tar
    -  blobs.2017-05-25-13-00-00.tar

Again, with a full backup.

    >>> write('blobs', 'one.txt', '26')
    >>> write('fs', '2017-05-26-12-00-00.fsz', 'Full fs backup 26')
    >>> backup_blobs_archive(
    ...     'blobs', 'backups', fs_backup_location='fs', timestamps=True,
    ...     compress_blob=False, incremental_blobs=True)
    >>> ls('backups')
    -  blobs.0.tar
    -  blobs.1.tar.gz
    -  blobs.2.tar
    -  blobs.2017-05-24-11-54-39.tar.gz
    -  blobs.2017-05-25-12-00-00.tar
    -  blobs.2017-05-25-13-00-00.tar
    -  blobs.2017-05-26-12-00-00.snar
    -  blobs.2017-05-26-12-00-00.tar

Again, with a delta.
We sleep, because --listed-incremental compares timestamps,
and this goes per second.
In practice, blobs do not get changed, only added or deleted.

    >>> time.sleep(1)
    >>> write('blobs', 'one.txt', '26.1')
    >>> write('fs', '2017-05-26-13-00-00.deltafsz', 'Delta fs backup 26.1')
    >>> backup_blobs_archive(
    ...     'blobs', 'backups', fs_backup_location='fs', timestamps=True,
    ...     compress_blob=False, incremental_blobs=True)
    >>> ls('backups')
    -  blobs.0.tar
    -  blobs.1.tar.gz
    -  blobs.2.tar
    -  blobs.2017-05-24-11-54-39.tar.gz
    -  blobs.2017-05-25-12-00-00.tar
    -  blobs.2017-05-25-13-00-00.tar
    -  blobs.2017-05-26-12-00-00.snar
    -  blobs.2017-05-26-12-00-00.tar
    -  blobs.2017-05-26-13-00-00.delta.tar

Now without file storage backups.

    >>> backup_blobs_archive(
    ...     'blobs', 'backups', fs_backup_location=None, timestamps=True,
    ...     compress_blob=False, incremental_blobs=True)
    >>> ls('backups')
    -  blobs.0.tar
    -  blobs.1.tar.gz
    -  blobs.2.tar
    -  blobs.2017-05-24-11-54-39.tar.gz
    -  blobs.2017-05-25-12-00-00.tar
    -  blobs.2017-05-25-13-00-00.tar
    -  blobs.2017-05-26-12-00-00.snar
    -  blobs.2017-05-26-12-00-00.tar
    -  blobs.2017-05-26-13-00-00.delta.tar
    -  blobs.20...-...-...-...-...-....delta.tar

Change one file, and remove another.

    >>> write('blobs', 'one.txt', '26.2')
    >>> ls('blobs')
    d  dir
    -  four.txt
    -  one.txt
    -  three.txt
    >>> ls('blobs', 'dir')
    >>> cat('blobs', 'one.txt')
    26.2
    >>> remove('blobs', 'three.txt')

Test a restore. This should restore the previous blob contents.

    >>> restore_blobs_archive('backups', 'blobs', timestamps=True)
    >>> ls('blobs')
    d  dir
    -  four.txt
    -  one.txt
    -  three.txt
    >>> ls('blobs', 'dir')
    >>> cat('blobs', 'one.txt')
    26.1

Backup again, with a pause and with full backup.

    >>> time.sleep(1)
    >>> remove('blobs', 'four.txt')
    >>> write('blobs', 'one.txt', 'new')
    >>> backup_blobs_archive(
    ...     'blobs', 'backups', fs_backup_location=None, timestamps=True,
    ...     compress_blob=False, incremental_blobs=True, full=True)
    >>> ls('backups')
    -  blobs.0.tar
    -  blobs.1.tar.gz
    -  blobs.2.tar
    -  blobs.2017-05-24-11-54-39.tar.gz
    -  blobs.2017-05-25-12-00-00.tar
    -  blobs.2017-05-25-13-00-00.tar
    -  blobs.2017-05-26-12-00-00.snar
    -  blobs.2017-05-26-12-00-00.tar
    -  blobs.2017-05-26-13-00-00.delta.tar
    -  blobs.20...-...-...-...-...-....delta.tar
    -  blobs.20...-...-...-...-...-....snar
    -  blobs.20...-...-...-...-...-....tar

Test restores to several timestamps.

    >>> restore_blobs_archive('backups', 'blobs', timestamps=True)
    >>> ls('blobs')
    d  dir
    -  one.txt
    -  three.txt
    >>> ls('blobs', 'dir')
    >>> cat('blobs', 'one.txt')
    new
    >>> restore_blobs_archive(
    ...     'backups', 'blobs', timestamps=True, date='2017-05-26-13-00-00')
    >>> ls('blobs')
    d  dir
    -  four.txt
    -  one.txt
    -  three.txt
    >>> ls('blobs', 'dir')
    >>> cat('blobs', 'one.txt')
    26.1
    >>> restore_blobs_archive(
    ...    'backups', 'blobs', timestamps=True, date='2017-05-26-12-00-00')
    >>> ls('blobs')
    d  dir
    -  four.txt
    -  one.txt
    -  three.txt
    >>> ls('blobs', 'dir')
    >>> cat('blobs', 'one.txt')
    26

Cleanup:

    >>> remove('blobs')
    >>> remove('backups')
    >>> remove('fs')
