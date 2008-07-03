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
        datafs = os.path.abspath(
            os.path.join(buildout_dir, 'var', 'filestorage', 'Data.fs'))

        options.setdefault('buildout_dir', buildout_dir)
        options.setdefault('location', backup_dir)
        options.setdefault('keep', '2')
        options.setdefault('datafs', datafs)

        self.egg = zc.recipe.egg.Egg(buildout, options['recipe'], options)

        python = buildout['buildout']['python']
        options['executable'] = buildout[python]['executable']
        options['bin-directory'] = buildout['buildout']['bin-directory']
        self.options = options

    def install(self):
        """Installer"""
        backup_dir = os.path.abspath(self.options['location'])
        if not os.path.isdir(backup_dir):
            os.makedirs(backup_dir)
            logger.info('Created %s', backup_dir)

        buildout_dir = self.buildout['buildout']['directory']
        datafs = os.path.join(buildout_dir, self.options['datafs'])
        backup_location = os.path.join(buildout_dir,
                                       self.options['location'])
        initialization = '\n'.join(
            ["bin_dir = '%s'" % self.options['bin-directory'],
             "datafs = '%s'" % datafs,
             "keep = '%s'" % self.options['keep'],
             "backup_location = '%s'" % backup_location,
             ])
        requirements, ws = self.egg.working_set(['collective.recipe.backup'])
        scripts = zc.buildout.easy_install.scripts(
            [('backup', 'collective.recipe.backup.repozorunner', 'main')],
            #requirements,
            ws, self.options['executable'], self.options['bin-directory'],
            arguments='bin_dir, datafs, backup_location, keep',
            initialization=initialization)
        # Return files that were created by the recipe. The buildout
        # will remove all returned files upon reinstall.
        return scripts

    def update(self):
        """Updater"""
        pass
