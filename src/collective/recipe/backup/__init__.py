# -*- coding: utf-8 -*-
"""Recipe backup"""
import logging
import os

import zc.recipe.egg
import zc.buildout

logger = logging.getLogger('backup')

if hasattr(zc.buildout.easy_install, 'sitepackage_safe_scripts'):
    # zc.buildout 1.5
    USE_SAFE_SCRIPTS = True
else:
    # zc.buildout 1.4 or earlier
    USE_SAFE_SCRIPTS = False
# Using safe scripts sounds nice, but with that and a proper system
# python I somehow get this error when calling bin/repozo within one
# of our scripts, without an actual way to get that traceback:
#
# 'import site' failed; use -v for traceback
#
# So we will not use it after all.  It does not seem very needed
# either, as we are not importing any modules from outside the python
# core..
USE_SAFE_SCRIPTS = False


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
        # These must be four distinct locations.
        locations = {}
        for opt in ('location', 'snapshotlocation',
                    'blobbackuplocation', 'blobsnapshotlocation'):
            value = options.get(opt)
            if value:
                locations[opt] = value
        if len(locations.keys()) != len(set(locations.values())):
            raise zc.buildout.UserError(
                "These must be four distinct locations:\n",
                '\n'.join([('%s = %s' % (k, v)) for (k, v) in
                             sorted(locations.items())]))
        options.setdefault('pre_command', '')
        options.setdefault('post_command', '')
        options.setdefault('keep', '2')
        options.setdefault('keep_blob_days', '14')  # two weeks
        options.setdefault('datafs', datafs)
        options.setdefault('full', 'false')
        options.setdefault('debug', 'false')
        options.setdefault('gzip', 'true')
        options.setdefault('additional_filestorages', '')
        options.setdefault('enable_snapshotrestore', 'true')
        options.setdefault('use_rsync', 'true')
        options.setdefault('only_blobs', 'false')
        # Accept both blob-storage (used by plone.recipe.zope2instance
        # and friends) and blob_storage (as we use underscores
        # everywhere).
        options.setdefault('blob-storage', '')
        options.setdefault('blob_storage', '')
        if options['blob-storage'] != options['blob_storage']:
            if options['blob-storage'] and options['blob_storage']:
                # Both options have been set explicitly, which is
                # wrong.
                raise zc.buildout.UserError(
                    "Both blob_storage and blob-storage have been set. "
                    "Please pick one.")
        blob_storage = options['blob-storage'] or options['blob_storage']
        if not blob_storage:
            # Try to get the blob-storage location from the
            # instance/zeoclient/zeoserver part, if it is available.
            blob_recipes = (
                'plone.recipe.zeoserver',
                'plone.recipe.zope2instance',
                'plone.recipe.zope2zeoserver',
                )
            parts = buildout['buildout']['parts']
            part_names = parts.split()
            blob_storage = ''
            for part_name in part_names:
                part = self.buildout[part_name]
                if part.get('recipe') in blob_recipes:
                    blob_storage = part.get('blob-storage')
                    if blob_storage:
                        break
            if not blob_storage:
                # 'None' would give a TypeError when setting the option.
                blob_storage = ''
        # Make sure the options are the same, for good measure.
        options['blob-storage'] = options['blob_storage'] = blob_storage

        # We usually want backup_blobs to be true, but we should not
        # complain when there really is no blob-storage.
        options.setdefault('backup_blobs', '')
        if options['backup_blobs'] == '':
            if bool(blob_storage):
                options['backup_blobs'] = 'True'
            else:
                options['backup_blobs'] = 'False'

        self.egg = zc.recipe.egg.Egg(buildout, options['recipe'], options)

        python = buildout['buildout']['python']
        options['executable'] = buildout[python]['executable']
        options['bin-directory'] = buildout['buildout']['bin-directory']
        options['backup_name'] = backup_name
        options['snapshot_name'] = snapshot_name
        options['restore_name'] = restore_name
        options['snapshotrestore_name'] = snapshotrestore_name
        check_for_true(options, ['full', 'debug', 'gzip', 'only_blobs',
                                 'backup_blobs', 'use_rsync'])

        # For site_py_dest in scripts generated with buildout 1.5+:
        options['parts-directory'] = os.path.join(
            buildout['buildout']['parts-directory'], self.name)
        self.options = options

    def install(self):
        """Installer"""
        buildout_dir = self.options['buildout_dir']
        backup_location = construct_path(
            buildout_dir, self.options['location'])
        snapshot_location = construct_path(
            buildout_dir, self.options['snapshotlocation'])
        if self.options['only_blobs'] == 'False':
            if not os.path.isdir(backup_location):
                os.makedirs(backup_location)
                logger.info('Created %s', backup_location)
            if not os.path.isdir(snapshot_location):
                os.makedirs(snapshot_location)
                logger.info('Created %s', snapshot_location)

        # Blob backup.
        if self.options['backup_blobs'] == 'True' and \
               self.options['blob_storage']:
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
import sys
# Allow the user to make the script more quiet (say in a cronjob):
if sys.argv[-1] in ('-q', '--quiet'):
    loglevel = logging.WARN
logging.basicConfig(level=loglevel,
    format='%%(levelname)s: %%(message)s')
"""
        arguments_template = """
        bin_dir=%(bin-directory)r,
        datafs=%(datafs)r,
        keep=%(keep)s,
        keep_blob_days=%(keep_blob_days)s,
        backup_location=%(backup_location)r,
        snapshot_location=%(snapshot_location)r,
        blob_backup_location=%(blob_backup_location)r,
        blob_snapshot_location=%(blob_snapshot_location)r,
        blob_storage_source=%(blob_storage_source)r,
        full=%(full)s,
        verbose=%(debug)s,
        gzip=%(gzip)s,
        additional=%(additional)r,
        only_blobs=%(only_blobs)s,
        backup_blobs=%(backup_blobs)s,
        use_rsync=%(use_rsync)s,
        pre_command=%(pre_command)r,
        post_command=%(post_command)r,
        """
        # Work with a copy of the options, for safety.
        opts = self.options.copy()
        opts['loglevel'] = loglevel
        opts['datafs'] = datafs
        opts['backup_location'] = backup_location
        opts['snapshot_location'] = snapshot_location
        opts['blob_backup_location'] = blob_backup_location
        opts['blob_snapshot_location'] = blob_snapshot_location
        opts['blob_storage_source'] = opts['blob_storage']
        opts['additional'] = additional

        if opts['backup_blobs'] == 'False' and opts['only_blobs'] == 'True':
            raise zc.buildout.UserError(
                "Cannot have backup_blobs false and only_blobs true.")
        if opts['backup_blobs'] == 'True' and not opts['blob_storage']:
            raise zc.buildout.UserError(
                "backup_blobs is true, but no blob_storage could be found.")

        # Keep list of generated files/directories/scripts
        generated = []
        if USE_SAFE_SCRIPTS and not os.path.exists(opts['parts-directory']):
            # zc.buildout 1.5 wants to put a site.py into this parts
            # directory (indicated by site_py_dest) when site-packages
            # safe scripts are created.
            os.mkdir(opts['parts-directory'])
            generated.append(opts['parts-directory'])

        # Handle a few alternative spellings:
        opts['bin_dir'] = opts['bin-directory']
        opts['verbose'] = opts['debug']

        # Get general options for all scripts.
        initialization = initialization_template % opts
        orig_distributions, working_set = self.egg.working_set(
            ['collective.recipe.backup', 'zc.buildout', 'zc.recipe.egg'])
        executable = self.options['executable']
        dest = self.options['bin-directory']
        site_py_dest = self.options['parts-directory']
        script_arguments = arguments_template % opts
        creation_args = dict(
            dest=dest, working_set=working_set, executable=executable,
            site_py_dest=site_py_dest, initialization=initialization,
            script_arguments=script_arguments)

        # Create backup script
        reqs = [(self.options['backup_name'],
                 'collective.recipe.backup.main',
                 'backup_main')]
        creation_args['reqs'] = reqs
        generated += create_script(**creation_args)

        # Create backup snapshot script
        reqs = [(self.options['snapshot_name'],
                 'collective.recipe.backup.main',
                 'snapshot_main')]
        creation_args['reqs'] = reqs
        generated += create_script(**creation_args)

        # Create restore script
        reqs = [(self.options['restore_name'],
                 'collective.recipe.backup.main',
                 'restore_main')]
        creation_args['reqs'] = reqs
        generated += create_script(**creation_args)

        # Create snapshot restore script
        if self.options['enable_snapshotrestore'] == 'true':
            reqs = [(self.options['snapshotrestore_name'],
                     'collective.recipe.backup.main',
                     'snapshot_restore_main')]
            creation_args['reqs'] = reqs
            generated += create_script(**creation_args)

        # Return files that were created by the recipe. The buildout
        # will remove all returned files upon reinstall.
        return generated

    # When updating, do the same as when installing.  This is the
    # easiest, really.  And it is needed in case someone manually
    # removes e.g. var/backups or when the blob-storage location as
    # indicated in a plone.recipe.zope2instance or similar part has
    # changed.
    update = install


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


def create_script(**kwargs):
    """Create a script.

    Do this in a way that is compatible with zc.buildout 1.4 and 1.5
    (using the sitepackage_safe_scripts in the latter case).

    See http://pypi.python.org/pypi/zc.buildout/1.5.2
    section: #updating-recipes-to-support-a-system-python
    """
    if USE_SAFE_SCRIPTS:
        # zc.buildout 1.5
        script = zc.buildout.easy_install.sitepackage_safe_scripts(
            kwargs.get('dest'), kwargs.get('working_set'),
            kwargs.get('executable'), kwargs.get('site_py_dest'),
            reqs=kwargs.get('reqs'),
            script_arguments=kwargs.get('script_arguments'),
            initialization=kwargs.get('initialization'))
    else:
        # zc.buildout 1.4 or earlier
        script = zc.buildout.easy_install.scripts(
            kwargs.get('reqs'), kwargs.get('working_set'),
            kwargs.get('executable'), kwargs.get('dest'),
            arguments=kwargs.get('script_arguments'),
            initialization=kwargs.get('initialization'))
    return script
