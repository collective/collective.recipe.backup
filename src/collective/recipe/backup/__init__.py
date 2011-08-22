# -*- coding: utf-8 -*-
"""Recipe backup"""
import logging
import os

import zc.recipe.egg
import zc.buildout

logger = logging.getLogger('backup')


class Recipe(object):
    """zc.buildout recipe"""

    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options
        # self.buildout['buildout']['directory'] is not always the
        # main directory, but is the directory that contains the
        # config file, so if you do 'main/bin/buildout -c
        # conf/prod.cfg' the 'directory' is main/conf instead of the
        # expected main.  So we use the parent of the bin-directory
        # instead.
        #buildout_dir = self.buildout['buildout']['directory']
        bin_dir = self.buildout['buildout']['bin-directory']
        buildout_dir = os.path.join(bin_dir, os.path.pardir)
        if self.name == 'backup':
            backup_name = 'backup'
            snapshot_name = 'snapshotbackup'
            restore_name = 'restore'
            snapshotrestore_name = 'snapshotrestore'
            blob_backup_name = 'blobstoragebackup'
            blob_snapshot_name = 'blobstoragesnapshot'
        else:
            backup_name = self.name
            snapshot_name = self.name + '-snapshot'
            restore_name = self.name + '-restore'
            snapshotrestore_name = self.name + '-snapshotrestore'
            blob_backup_name = self.name + '-blobstorage'
            blob_snapshot_name = self.name + '-blobstoragesnapshot'

        backup_dir = os.path.abspath(
            os.path.join(buildout_dir, 'var', backup_name + 's'))
        snapshot_dir = os.path.abspath(
            os.path.join(buildout_dir, 'var', snapshot_name + 's'))
        datafs = os.path.abspath(
            os.path.join(buildout_dir, 'var', 'filestorage', 'Data.fs'))
        blob_backup_dir = os.path.abspath(
            os.path.join(buildout_dir, 'var', blob_backup_name + 's'))
        blob_snapshot_dir = os.path.abspath(
            os.path.join(buildout_dir, 'var', blob_snapshot_name + 's'))

        options.setdefault('buildout_dir', buildout_dir)
        options.setdefault('location', backup_dir)
        options.setdefault('snapshotlocation', snapshot_dir)
        options.setdefault('blobbackuplocation', blob_backup_dir)
        options.setdefault('blobsnapshotlocation', blob_snapshot_dir)
        options.setdefault('keep', '2')
        options.setdefault('datafs', datafs)
        options.setdefault('full', 'false')
        options.setdefault('debug', 'false')
        options.setdefault('gzip', 'true')
        options.setdefault('additional_filestorages', '')
        options.setdefault('enable_snapshotrestore', 'true')
        options.setdefault('blob-storage', '')
        options.setdefault('only_blobs', 'false')
        options.setdefault('backup_blobs', 'true')
        self.egg = zc.recipe.egg.Egg(buildout, options['recipe'], options)

        python = buildout['buildout']['python']
        options['executable'] = buildout[python]['executable']
        options['bin-directory'] = buildout['buildout']['bin-directory']
        options['backup_name'] = backup_name
        options['snapshot_name'] = snapshot_name
        options['restore_name'] = restore_name
        options['snapshotrestore_name'] = snapshotrestore_name
        check_for_true(options, ['full', 'debug', 'gzip', 'only_blobs',
                                 'backup_blobs'])
        self.options = options

    def install(self):
        """Installer"""
        buildout_dir = self.options['buildout_dir']
        backup_location = construct_path(
            buildout_dir, self.options['location'])
        snapshot_location = construct_path(
            buildout_dir, self.options['snapshotlocation'])
        if not os.path.isdir(backup_location):
            os.makedirs(backup_location)
            logger.info('Created %s', backup_location)
        if not os.path.isdir(snapshot_location):
            os.makedirs(snapshot_location)
            logger.info('Created %s', snapshot_location)

        # Blob backup.
        if self.options['blob-storage']:
            blob_backup_location = construct_path(
                buildout_dir, self.options['blobbackuplocation'])
            blob_snapshot_location = construct_path(
                buildout_dir, self.options['blobsnapshotlocation'])
            if not os.path.isdir(blob_backup_location):
                os.makedirs(blob_backup_location)
                logger.info('Created %s', blob_backup_location)
            if not os.path.isdir(blob_snapshot_location):
                os.makedirs(blob_snapshot_location)
                logger.info('Created %s', blob_snapshot_location)
        else:
            blob_backup_location = ''
            blob_snapshot_location = ''

        additional = self.options['additional_filestorages']
        if additional:
            additional = additional.split('\n')
            additional = [a.strip() for a in additional
                          if a.strip()]
        else:
            additional = []

        for a in additional:
            backup = backup_location + '_' + a
            snapshot = snapshot_location + '_' + a
            if not os.path.isdir(backup):
                os.makedirs(backup)
                logger.info('Created %s', backup)
            if not os.path.isdir(snapshot):
                os.makedirs(snapshot)
                logger.info('Created %s', snapshot)

        datafs = construct_path(buildout_dir, self.options['datafs'])
        if self.options['debug'] == 'True':
            loglevel = 'DEBUG'
        else:
            loglevel = 'INFO'
        initialization_template = """
import logging
loglevel = logging.%(loglevel)s
# Allow the user to make the script more quiet (say in a cronjob):
if sys.argv[-1] in ('-q', '--quiet'):
    loglevel = logging.WARN
logging.basicConfig(level=loglevel,
    format='%%(levelname)s: %%(message)s')
bin_dir = %(bin-directory)r
datafs = %(datafs)r
keep = %(keep)s
backup_location = %(backup_location)r
snapshot_location = %(snapshot_location)r
blob_backup_location = %(blob_backup_location)r
blob_snapshot_location = %(blob_snapshot_location)r
blob_storage_source = %(blob_storage_source)r
full = %(full)s
verbose = %(debug)s
gzip = %(gzip)s
additional = %(additional)r
only_blobs = %(only_blobs)s
backup_blobs = %(backup_blobs)s
"""
        # Work with a copy of the options, for safety.
        opts = self.options.copy()
        opts['loglevel'] = loglevel
        opts['datafs'] = datafs
        opts['backup_location'] = backup_location
        opts['snapshot_location'] = snapshot_location
        opts['blob_backup_location'] = blob_backup_location
        opts['blob_snapshot_location'] = blob_snapshot_location
        opts['blob_storage_source'] = opts['blob-storage']
        opts['additional'] = additional

        if opts['backup_blobs'] == 'False' and opts['only_blobs'] == 'True':
            raise zc.buildout.UserError(
                "Cannot have backup_blobs false and only_blobs true.")

        initialization = initialization_template % opts
        requirements, ws = self.egg.working_set(['collective.recipe.backup',
                                                 'zc.buildout',
                                                 'zc.recipe.egg'])
        scripts = zc.buildout.easy_install.scripts(
            [(self.options['backup_name'],
              'collective.recipe.backup.main',
              'backup_main')],
            #requirements,
            ws, self.options['executable'], self.options['bin-directory'],
            # Note: no commas at the end of lines in the arguments; it
            # must not be a tuple, it is just string concatenation.
            arguments=('bin_dir, datafs, backup_location, '
                       'keep, full, verbose, gzip, additional, '
                       'blob_backup_location, blob_storage_source, '
                       'backup_blobs, only_blobs'),
            initialization=initialization)
        scripts += zc.buildout.easy_install.scripts(
            [(self.options['snapshot_name'],
              'collective.recipe.backup.main',
              'snapshot_main')],
            #requirements,
            ws, self.options['executable'], self.options['bin-directory'],
            # Note: no commas at the end of lines in the arguments; it
            # must not be a tuple, it is just string concatenation.
            arguments=('bin_dir, datafs, snapshot_location, keep, '
                       'verbose, gzip, additional, blob_snapshot_location, '
                       'blob_storage_source, backup_blobs, only_blobs'),
            initialization=initialization)
        scripts += zc.buildout.easy_install.scripts(
            [(self.options['restore_name'],
              'collective.recipe.backup.main',
              'restore_main')],
            #requirements,
            ws, self.options['executable'], self.options['bin-directory'],
            # Note: no commas at the end of lines in the arguments; it
            # must not be a tuple, it is just string concatenation.
            arguments=('bin_dir, datafs, backup_location, verbose, '
                       'additional, blob_backup_location, '
                       'blob_storage_source, backup_blobs, only_blobs'),
            initialization=initialization)
        if self.options['enable_snapshotrestore'] == 'true':
            scripts += zc.buildout.easy_install.scripts(
                [(self.options['snapshotrestore_name'],
                  'collective.recipe.backup.main',
                  'restore_main')],
                #requirements,
                ws, self.options['executable'], self.options['bin-directory'],
                # Note: no commas at the end of lines in the arguments; it
                # must not be a tuple, it is just string concatenation.
                arguments=('bin_dir, datafs, snapshot_location, verbose, '
                           'additional, blob_snapshot_location, '
                           'blob_storage_source, backup_blobs, only_blobs'),
                initialization=initialization)
        # Return files that were created by the recipe. The buildout
        # will remove all returned files upon reinstall.
        return scripts

    def update(self):
        """Updater"""
        pass


def check_for_true(options, keys):
    """Set the truth options right.

    Default value is False, set it to True only if we're passed the string
    'true' or 'True'. Unify on a capitalized True/False string.

    """
    for key in keys:
        if options[key].lower() == 'true':
            options[key] = 'True'
        else:
            options[key] = 'False'


def construct_path(buildout_dir, path):
    """Return absolute path, taking into account buildout dir and ~ expansion.

    Normal paths are relative to the buildout dir::

      >>> buildout_dir = '/somewhere/buildout'
      >>> construct_path(buildout_dir, 'var/filestorage/Data.fs')
      '/somewhere/buildout/var/filestorage/Data.fs'

    Absolute paths also work::

      >>> construct_path(buildout_dir, '/var/filestorage/Data.fs')
      '/var/filestorage/Data.fs'

    And a tilde, too::

      >>> userdir = os.path.expanduser('~')
      >>> desired = userdir + '/var/filestorage/Data.fs'
      >>> result = construct_path(buildout_dir, '~/var/filestorage/Data.fs')
      >>> result == desired
      True

    Relative links are nicely normalized::

      >>> construct_path(buildout_dir, '../var/filestorage/Data.fs')
      '/somewhere/var/filestorage/Data.fs'

    Also $HOME-style environment variables are expanded::

      >>> import os
      >>> os.environ['BACKUPDIR'] = '/var/backups'
      >>> construct_path(buildout_dir, '$BACKUPDIR/myproject')
      '/var/backups/myproject'

    """
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    combination = os.path.join(buildout_dir, path)
    normalized = os.path.normpath(combination)
    return normalized
