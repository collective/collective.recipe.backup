# -*- coding: utf-8 -*-
"""Recipe backup"""
import logging
import os
import sys

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

        options.setdefault('location', backup_dir)
        options.setdefault('scripts', '')

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

        requirements, ws = self.egg.working_set(['collective.recipe.backup'])
        scripts = zc.buildout.easy_install.scripts(
            #[('backup', 'collective.recipe.backup.repozorunner', 'main')],
            requirements,
            ws, self.options['executable'], self.options['bin-directory'])


        # Return files that were created by the recipe. The buildout
        # will remove all returned files upon reinstall.
        return tuple()

    def update(self):
        """Updater"""
        pass
