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
        buildout_dir = self.buildout['buildout']['directory']
        backup_dir = os.path.abspath(
            os.path.join(buildout_dir, 'var', 'backups'))
        snapshot_dir = os.path.abspath(
            os.path.join(buildout_dir, 'var', 'snapshotbackups'))
        datafs = os.path.abspath(
            os.path.join(buildout_dir, 'var', 'filestorage', 'Data.fs'))

        options.setdefault('buildout_dir', buildout_dir)
        options.setdefault('location', backup_dir)
        options.setdefault('snapshotlocation', snapshot_dir)
        options.setdefault('keep', '2')
        options.setdefault('datafs', datafs)
        options.setdefault('full', 'false')
        options.setdefault('debug', 'false')
        options.setdefault('gzip', 'false')
        options.setdefault('additional_filestorages', '')

        self.egg = zc.recipe.egg.Egg(buildout, options['recipe'], options)

        python = buildout['buildout']['python']
        options['executable'] = buildout[python]['executable']
        options['bin-directory'] = buildout['buildout']['bin-directory']
        check_for_true(options, ['full', 'debug', 'gzip'])
        self.options = options

    def install(self):
        """Installer"""
        backup_location = os.path.abspath(self.options['location'])
        snapshot_location = os.path.abspath(self.options['snapshotlocation'])
        if not os.path.isdir(backup_location):
            os.makedirs(backup_location)
            logger.info('Created %s', backup_location)
        if not os.path.isdir(snapshot_location):
            os.makedirs(snapshot_location)
            logger.info('Created %s', snapshot_location)

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

        buildout_dir = self.buildout['buildout']['directory']
        datafs = os.path.join(buildout_dir, self.options['datafs'])
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
bin_dir = '%(bin-directory)s'
datafs = '%(datafs)s'
keep = %(keep)s
backup_location = '%(backup_location)s'
snapshot_location = '%(snapshot_location)s'
full = %(full)s
verbose = %(debug)s
gzip = %(gzip)s
additional = %(additional)r
"""
        # Work with a copy of the options, for safety.
        opts = self.options.copy()
        opts['loglevel'] = loglevel
        opts['datafs'] = datafs
        opts['backup_location'] = backup_location
        opts['snapshot_location'] = snapshot_location
        opts['additional'] = additional
        initialization = initialization_template % opts
        requirements, ws = self.egg.working_set(['collective.recipe.backup',
                                                 'zc.buildout',
                                                 'zc.recipe.egg'])
        scripts = zc.buildout.easy_install.scripts(
            [('backup', 'collective.recipe.backup.repozorunner',
              'backup_main')],
            #requirements,
            ws, self.options['executable'], self.options['bin-directory'],
            arguments='bin_dir, datafs, backup_location, keep, full, verbose, gzip, additional',
            initialization=initialization)
        scripts = zc.buildout.easy_install.scripts(
            [('snapshotbackup', 'collective.recipe.backup.repozorunner',
              'snapshot_main')],
            #requirements,
            ws, self.options['executable'], self.options['bin-directory'],
            arguments='bin_dir, datafs, snapshot_location, keep, verbose, gzip, additional',
            initialization=initialization)
        scripts = zc.buildout.easy_install.scripts(
            [('restore', 'collective.recipe.backup.repozorunner',
              'restore_main')],
            #requirements,
            ws, self.options['executable'], self.options['bin-directory'],
            arguments='bin_dir, datafs, backup_location, verbose, additional',
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
