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

        self.egg = zc.recipe.egg.Egg(buildout, options['recipe'], options)

        python = buildout['buildout']['python']
        options['executable'] = buildout[python]['executable']
        options['bin-directory'] = buildout['buildout']['bin-directory']
        if options['full'].lower() == 'true':
            options['full'] = 'True'
        else:
            options['full'] = 'False'
        if options['debug'].lower() == 'true':
            options['debug'] = 'True'
        else:
            options['debug'] = 'False'
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

        buildout_dir = self.buildout['buildout']['directory']
        datafs = os.path.join(buildout_dir, self.options['datafs'])
        if self.options['debug'] == 'True':
            loglevel = 'DEBUG'
        else:
            loglevel = 'INFO'
        initialization = '\n'.join(
            ["import logging",
             "logging.basicConfig(level=logging.%s," % loglevel,
             "    format='%(levelname)s: %(message)s')",
             "bin_dir = '%s'" % self.options['bin-directory'],
             "datafs = '%s'" % datafs,
             "keep = %s" % self.options['keep'],
             "backup_location = '%s'" % backup_location,
             "snapshot_location = '%s'" % snapshot_location,
             "full = %s" % self.options['full'],
             "verbose = %s" % self.options['debug'],
             ])
        requirements, ws = self.egg.working_set(['collective.recipe.backup'])
        scripts = zc.buildout.easy_install.scripts(
            [('backup', 'collective.recipe.backup.repozorunner', 'backup_main')],
            #requirements,
            ws, self.options['executable'], self.options['bin-directory'],
            arguments='bin_dir, datafs, backup_location, keep, full, verbose',
            initialization=initialization)
        scripts = zc.buildout.easy_install.scripts(
            [('snapshotbackup', 'collective.recipe.backup.repozorunner', 'snapshot_main')],
            #requirements,
            ws, self.options['executable'], self.options['bin-directory'],
            arguments='bin_dir, datafs, snapshot_location, keep, verbose',
            initialization=initialization)
        scripts = zc.buildout.easy_install.scripts(
            [('restore', 'collective.recipe.backup.repozorunner', 'restore_main')],
            #requirements,
            ws, self.options['executable'], self.options['bin-directory'],
            arguments='bin_dir, datafs, backup_location, verbose',
            initialization=initialization)
        # Return files that were created by the recipe. The buildout
        # will remove all returned files upon reinstall.
        return scripts

    def update(self):
        """Updater"""
        pass
