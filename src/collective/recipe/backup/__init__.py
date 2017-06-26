# -*- coding: utf-8 -*-
"""Recipe backup"""
from collective.recipe.backup import utils

import logging
import os
import pprint
import re
import sys
import zc.buildout
import zc.recipe.egg


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

        # Accept both blob-storage (used by plone.recipe.zope2instance
        # and friends) and blob_storage (as we use underscores
        # everywhere).  But keep only blob_storage.
        blobs_1 = options.pop('blob-storage', '')
        options.setdefault('blob_storage', blobs_1).rstrip(os.sep)
        blobs_2 = options.get('blob_storage')
        if blobs_1 != blobs_2:
            if blobs_1 and blobs_2:
                # Both options have been set explicitly, which is
                # wrong.
                raise zc.buildout.UserError(
                    "Both blob_storage and blob-storage have been set. "
                    "Please pick one.")

        # We usually want backup_blobs to be true.  If no blob_storage is
        # found, we complain, unless backup_blobs has explicitly been disabled.
        # Or when the Python version is lower than 2.6: we then expect Plone 3,
        # so no blob storage.
        if sys.version_info >= (2, 6):
            options.setdefault('backup_blobs', 'True')
        else:
            options.setdefault('backup_blobs', 'False')

        # Validate options, checking for example that the locations are unique.
        self.validate()

    def install(self):
        """Installer"""
        options = self.options
        buildout = self.buildout
        # self.buildout['buildout']['directory'] is not always the
        # main directory, but is the directory that contains the
        # config file, so if you do 'main/bin/buildout -c
        # conf/prod.cfg' the 'directory' is main/conf instead of the
        # expected main.  So we use the parent of the bin-directory
        # instead.
        bin_dir = self.buildout['buildout']['bin-directory']
        buildout_dir = os.path.join(bin_dir, os.path.pardir)
        if self.name == 'backup':
            backup_name = 'backup'
            fullbackup_name = 'fullbackup'
            zipbackup_name = 'zipbackup'
            snapshot_name = 'snapshotbackup'
            restore_name = 'restore'
            snapshotrestore_name = 'snapshotrestore'
            altrestore_name = 'altrestore'
            ziprestore_name = 'ziprestore'
            blob_backup_name = 'blobstoragebackup'
            blob_snapshot_name = 'blobstoragesnapshot'
            blob_zip_name = 'blobstoragezip'
        else:
            backup_name = self.name
            fullbackup_name = self.name + '-full'
            zipbackup_name = self.name + '-zip'
            snapshot_name = self.name + '-snapshot'
            restore_name = self.name + '-restore'
            snapshotrestore_name = self.name + '-snapshotrestore'
            altrestore_name = self.name + '-altrestore'
            ziprestore_name = self.name + '-ziprestore'
            blob_backup_name = self.name + '-blobstorage'
            blob_snapshot_name = self.name + '-blobstoragesnapshot'
            blob_zip_name = self.name + '-blobstoragezip'

        # Get var directory from instance/zeoclient/zeoserver part, if
        # available.  p.r.zeoserver has zeo-var option.
        var_dir = get_zope_option(self.buildout, 'zeo-var')
        if not var_dir:
            # p.r.zope2instance has var option
            var_dir = get_zope_option(self.buildout, 'var')
        if var_dir:
            var_dir = os.path.abspath(var_dir)
        else:
            var_dir = os.path.abspath(os.path.join(buildout_dir, 'var'))

        prefix = options.get('locationprefix')
        if prefix is not None:
            prefix = construct_path(buildout_dir, prefix)
        else:
            prefix = var_dir

        backup_dir = os.path.abspath(
            os.path.join(prefix, backup_name + 's'))
        snapshot_dir = os.path.abspath(
            os.path.join(prefix, snapshot_name + 's'))
        zip_backup_dir = os.path.abspath(
            os.path.join(prefix, zipbackup_name + 's'))
        blob_backup_dir = os.path.abspath(
            os.path.join(prefix, blob_backup_name + 's'))
        blob_snapshot_dir = os.path.abspath(
            os.path.join(prefix, blob_snapshot_name + 's'))
        blob_zip_dir = os.path.abspath(
            os.path.join(prefix, blob_zip_name + 's'))

        # file-storage may have been set in recipes
        datafs = get_zope_option(self.buildout, 'file-storage')
        if not datafs:
            datafs = os.path.abspath(
                os.path.join(var_dir, 'filestorage', 'Data.fs'))

        # locations, alphabetical
        options.setdefault('blobbackuplocation', blob_backup_dir)
        options.setdefault('blobsnapshotlocation', blob_snapshot_dir)
        options.setdefault('blobziplocation', blob_zip_dir)
        options.setdefault('buildout_dir', buildout_dir)
        options.setdefault('location', backup_dir)
        options.setdefault('snapshotlocation', snapshot_dir)
        options.setdefault('ziplocation', zip_backup_dir)

        # Validate options, checking that the locations are unique
        self.validate()

        # more options, alphabetical
        options.setdefault('additional_filestorages', '')
        options.setdefault('alternative_restore_sources', '')
        # archive_blob used to be called gzip_blob.
        options.setdefault('archive_blob', options.get('gzip_blob', 'false'))
        options.setdefault('blob_timestamps', 'false')
        options.setdefault('compress_blob', 'false')
        options.setdefault('datafs', datafs)
        options.setdefault('debug', 'false')
        options.setdefault('enable_fullbackup', 'false')
        options.setdefault('enable_snapshotrestore', 'true')
        options.setdefault('enable_zipbackup', 'false')
        options.setdefault('full', 'false')
        options.setdefault('gzip', 'true')
        options.setdefault('keep', '2')
        options.setdefault('keep_blob_days', '14')  # two weeks
        options.setdefault('only_blobs', 'false')
        options.setdefault('post_command', '')
        options.setdefault('pre_command', '')
        options.setdefault('quick', 'true')
        options.setdefault('rsync_options', '')
        options.setdefault('use_rsync', 'true')

        # Get the blob storage.
        blob_storage = options['blob_storage']
        if not blob_storage:
            # Try to get the blob-storage location from the
            # instance/zeoclient/zeoserver part, if it is available.
            blob_storage = get_zope_option(self.buildout, 'blob-storage')
            if not blob_storage:
                # The recipes put it in var/blobstorage by default.
                # But if there is no recipe, then we don't set this.
                if get_zope_option(self.buildout, 'recipe'):
                    blob_storage = os.path.abspath(
                        os.path.join(var_dir, 'blobstorage'))
                else:
                    # 'None' would give a TypeError when setting the option.
                    blob_storage = ''
            options['blob_storage'] = blob_storage
        # Validate again, which also makes sure the blob storage options are
        # the same, for good measure.
        self.validate()

        backup_blobs = to_bool(options['backup_blobs'])
        if backup_blobs and not blob_storage:
            raise zc.buildout.UserError(
                "No blob_storage found. You must specify one. "
                "To ignore this, set 'backup_blobs = false' "
                "in the [%s] section." % self.name)

        self.egg = zc.recipe.egg.Egg(buildout, options['recipe'], options)

        python = buildout['buildout']['python']
        options['executable'] = buildout[python]['executable']
        options['bin-directory'] = buildout['buildout']['bin-directory']
        options['backup_name'] = backup_name
        options['fullbackup_name'] = fullbackup_name
        options['zipbackup_name'] = zipbackup_name
        options['snapshot_name'] = snapshot_name
        options['restore_name'] = restore_name
        options['snapshotrestore_name'] = snapshotrestore_name
        options['ziprestore_name'] = ziprestore_name
        options['altrestore_name'] = altrestore_name

        # Validate agin, which also sets the truth values correctly.
        self.validate()

        # For site_py_dest in scripts generated with buildout 1.5+:
        options['parts-directory'] = os.path.join(
            buildout['buildout']['parts-directory'], self.name)

        # More locations.
        backup_location = construct_path(
            prefix, self.options['location'])
        snapshot_location = construct_path(
            prefix, self.options['snapshotlocation'])
        zip_location = construct_path(
            prefix, self.options['ziplocation'])

        # Blob backup.
        if to_bool(self.options['backup_blobs']):
            blob_backup_location = construct_path(
                prefix, self.options['blobbackuplocation'])
            blob_snapshot_location = construct_path(
                prefix, self.options['blobsnapshotlocation'])
            blob_zip_location = construct_path(
                prefix, self.options['blobziplocation'])
        else:
            blob_backup_location = ''
            blob_snapshot_location = ''
            blob_zip_location = ''

        additional = self.options['additional_filestorages']
        storages = []
        datafs = construct_path(buildout_dir, self.options['datafs'])
        filestorage_dir = os.path.split(datafs)[0]
        if additional:
            ADDITIONAL_REGEX = (
                r'^\s*(?P<storage>[^\s]+)'
                '\s*(?P<datafs>[^\s]*)'
                '\s*(?P<blobdir>[^\s]*)\s*$')
            for a in additional.split('\n'):
                if not a:
                    continue
                storage = re.match(ADDITIONAL_REGEX, a).groupdict()
                if storage['storage'] in [s['storage'] for s in storages]:
                    logger.warning(
                        'storage %s duplicated' % storage['storage'])
                if not storage['datafs']:
                    storage['datafs'] = os.path.join(
                        filestorage_dir, '%s.fs' % storage['storage'])
                storage['backup_location'] = backup_location + '_' + \
                    storage['storage']
                storage['snapshot_location'] = snapshot_location + '_' + \
                    storage['storage']
                storage['zip_location'] = zip_location + '_' + \
                    storage['storage']
                if storage['blobdir']:
                    storage['blob_backup_location'] = blob_backup_location \
                        and (blob_backup_location + '_' + storage['storage'])
                    storage['blob_snapshot_location'] = \
                        blob_snapshot_location and (blob_snapshot_location +
                                                    '_' + storage['storage'])
                    storage['blob_zip_location'] = \
                        blob_zip_location and (blob_zip_location +
                                               '_' + storage['storage'])
                storages.append(storage)

        # '1' is the default root storagename for Zope. The property
        # ``storage`` on this recipe currently is used only for
        # logging.
        storage = dict(
            storage="1",
            datafs=datafs,
            blobdir=self.options['blob_storage'],
            backup_location=backup_location,
            snapshot_location=snapshot_location,
            zip_location=zip_location,
        )

        if storage['blobdir']:
            storage['blob_backup_location'] = blob_backup_location
            storage['blob_snapshot_location'] = blob_snapshot_location
            storage['blob_zip_location'] = blob_zip_location
        storages.append(storage)

        if not to_bool(self.options['only_blobs']):
            for s in storages:
                backup_location = s['backup_location']
                snapshot_location = s['snapshot_location']
                utils.try_create_folder(backup_location)
                utils.try_create_folder(snapshot_location)

        # Blob backup.
        if to_bool(self.options['backup_blobs']):
            blob_storage_found = False
            for s in storages:
                if s['blobdir']:
                    s['blobdir'] = s['blobdir'].rstrip(os.sep)
                    blob_storage_found = True
                    blob_backup_location = s['blob_backup_location']
                    blob_snapshot_location = s['blob_snapshot_location']
                    utils.try_create_folder(blob_backup_location)
                    utils.try_create_folder(blob_snapshot_location)
            if not blob_storage_found:
                raise zc.buildout.UserError(
                    "backup_blobs is true, but no blob_storage could be "
                    "found.")

        # Handle alternative restore sources.
        alt_sources = self.options['alternative_restore_sources']
        if alt_sources:
            storage_keys = [s['storage'] for s in storages]
            alt_keys = []
            ALT_REGEX = (
                r'^\s*(?P<storage>[^\s]+)'
                '\s+(?P<datafs>[^\s]+)'
                '\s*(?P<blobdir>[^\s]*)\s*$')
            for a in alt_sources.split('\n'):
                if not a:
                    continue
                match = re.match(ALT_REGEX, a)
                if match is None:
                    raise zc.buildout.UserError(
                        "alternative_restore_sources line %r has a wrong "
                        "format. Should be: 'storage-name "
                        "filestorage-backup-path', optionally followed by "
                        "a blobstorage-backup-path." % a)
                source = match.groupdict()
                key = orig_key = source['storage']
                if key == 'Data':
                    key = '1'  # Data.fs is called storage '1'.
                if key not in storage_keys:
                    raise zc.buildout.UserError(
                        "alternative_restore_sources key %r unknown in "
                        "storages." % orig_key)
                alt_keys.append(key)
                storage = [s for s in storages if key == s['storage']][0]
                if storage.get('alt_location'):
                    # Duplicate key.
                    if key == '1':
                        raise zc.buildout.UserError(
                            "alternative_restore_sources key %r is used. "
                            "Are you using both '1' and 'Data'? They are "
                            "alternative keys for the same Data.fs."
                            % orig_key)
                    raise zc.buildout.UserError(
                        "alternative_restore_sources key %r is used twice."
                        % orig_key)
                storage['alt_location'] = construct_path(
                    buildout_dir, source['datafs'])
                blobdir = source['blobdir']
                if storage['blobdir']:
                    if not blobdir:
                        raise zc.buildout.UserError(
                            "alternative_restore_sources key %r is missing a "
                            "blobdir." % orig_key)
                    storage['blob_alt_location'] = construct_path(
                        buildout_dir, blobdir)
                elif blobdir:
                    raise zc.buildout.UserError(
                        "alternative_restore_sources key %r specifies "
                        "blobdir %r but the original storage has no "
                        "blobstorage." % (orig_key, blobdir))
                else:
                    storage['blob_alt_location'] = ''
            # Check that all original storages have an alternative.
            for key in storage_keys:
                if key not in alt_keys:
                    if key == '1':
                        key = 'Data'  # canonical spelling
                    raise zc.buildout.UserError(
                        "alternative_restore_sources is missing key %r. "
                        % key)

        if to_bool(self.options['debug']):
            loglevel = 'DEBUG'
        else:
            loglevel = 'INFO'
        initialization_template = """
import logging
loglevel = logging.%(loglevel)s
from optparse import OptionParser
parser = OptionParser()
# parser.add_option("-S", "--storage", dest="storage",
#                  action="store", type="string",
#                  help="storage name")
parser.add_option("-q", "--quiet",
                  action="store_false", dest="verbose", default=True,
                  help="don't print status messages to stdout")
parser.add_option("-n", "--no-prompt",
                  action="store_true", dest="no_prompt", default=False,
                  help="don't ask for any user confirmation")
(options, args) = parser.parse_args()
# storage = options.storage
# Allow the user to make the script more quiet (say in a cronjob):
if not options.verbose:
    loglevel = logging.WARN
log_format = '%%(levelname)s: %%(message)s'
if loglevel < logging.INFO:
    log_format = '%%(asctime)s ' + log_format
logging.basicConfig(level=loglevel,
    format=log_format)
"""
        arguments_template = """
        bin_dir=%(bin-directory)r,
        storages=%(storages)s,
        keep=%(keep)s,
        keep_blob_days=%(keep_blob_days)s,
        full=%(full)s,
        verbose=%(debug)s,
        gzip=%(gzip)s,
        quick=%(quick)s,
        only_blobs=%(only_blobs)s,
        backup_blobs=%(backup_blobs)s,
        use_rsync=%(use_rsync)s,
        rsync_options=%(rsync_options)r,
        archive_blob=%(archive_blob)s,
        compress_blob=%(compress_blob)s,
        pre_command=%(pre_command)r,
        post_command=%(post_command)r,
        no_prompt=options.no_prompt,
        blob_timestamps=%(blob_timestamps)s,
        """
        # Work with a copy of the options, for safety.
        opts = self.options.copy()
        opts['loglevel'] = loglevel
        opts['storages'] = pprint.pformat(storages)

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

        # Create full backup script
        if to_bool(self.options['enable_fullbackup']):
            reqs = [(self.options['fullbackup_name'],
                     'collective.recipe.backup.main',
                     'fullbackup_main')]
            creation_args['reqs'] = reqs
            generated += create_script(**creation_args)

        # Create zip backup script.
        if to_bool(self.options['enable_zipbackup']):
            reqs = [(self.options['zipbackup_name'],
                     'collective.recipe.backup.main',
                     'zipbackup_main')]
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

        # Create zip restore script.
        if to_bool(self.options['enable_zipbackup']):
            reqs = [(self.options['ziprestore_name'],
                     'collective.recipe.backup.main',
                     'zip_restore_main')]
            creation_args['reqs'] = reqs
            generated += create_script(**creation_args)

        # Create snapshot restore script
        if to_bool(self.options['enable_snapshotrestore']):
            reqs = [(self.options['snapshotrestore_name'],
                     'collective.recipe.backup.main',
                     'snapshot_restore_main')]
            creation_args['reqs'] = reqs
            generated += create_script(**creation_args)

        # Create alternative sources restore script
        if self.options['alternative_restore_sources']:
            reqs = [(self.options['altrestore_name'],
                     'collective.recipe.backup.main',
                     'alt_restore_main')]
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

    def validate(self):
        options = self.options
        check_for_true(
            options,
            ['full', 'debug', 'gzip', 'only_blobs',
             'backup_blobs', 'use_rsync', 'archive_blob',
             'quick', 'enable_snapshotrestore',
             'enable_zipbackup', 'enable_fullbackup',
             'compress_blob',
             'blob_timestamps'])

        # These must be distinct locations.
        locations = {}
        for opt in ('location', 'snapshotlocation',
                    'blobbackuplocation', 'blobsnapshotlocation',
                    'ziplocation', 'blobziplocation'):
            value = options.get(opt)
            if value:
                locations[opt] = value
        if len(locations.keys()) != len(set(locations.values())):
            raise zc.buildout.UserError(
                "These must be distinct locations:\n",
                '\n'.join([('%s = %s' % (k, v)) for (k, v) in
                           sorted(locations.items())]))

        if not to_bool(options.get('backup_blobs')):
            if to_bool(options.get('only_blobs')):
                raise zc.buildout.UserError(
                    "Cannot have backup_blobs false and only_blobs true.")
            if to_bool(options.get('enable_zipbackup')):
                raise zc.buildout.UserError(
                    "Cannot have backup_blobs false and enable_zipbackup "
                    "true. zipbackup is useless without blobs.")


def check_for_true(options, keys):
    """Set the truth options right.

    Default value is False, set it to True only if we're passed the string
    'true' or 'True'. Unify on a capitalized True/False string.

    """
    for key in keys:
        if key not in options:
            continue
        if to_bool(options[key]):
            options[key] = 'True'
        else:
            options[key] = 'False'


def to_bool(option):
    if option is None:
        return False
    if not isinstance(option, basestring):
        return bool(option)
    option = option.lower()
    return option in ('true', 'yes', 'on', '1')


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


def get_zope_option(buildout, option):
    """Try to get an option from another buildout part.

    For example the blob-storage location.

    We look in an instance/zeoclient/zeoserver part, if it is available.
    Well, we check specific recipes.
    """
    recipes = (
        'plone.recipe.zeoserver',
        'plone.recipe.zope2instance',
        'plone.recipe.zope2zeoserver',
    )
    parts = buildout['buildout']['parts']
    part_names = parts.split()
    value = None
    for part_name in part_names:
        part = buildout[part_name]
        if part.get('recipe', '').lower() in recipes:
            value = part.get(option)
            if value:
                break
    return value
