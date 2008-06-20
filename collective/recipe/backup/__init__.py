# -*- coding: utf-8 -*-
"""Recipe backup"""
import logging
import os
import sys

import zc.buildout


logger = logging.getLogger('backup')


class Recipe(object):
    """zc.buildout recipe"""

    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options
        buildout_dir = self.buildout['buildout']['directory']
        options['bin_dir'] = os.path.join(buildout_dir, 'bin')
        backup_dir = os.path.abspath(
            os.path.join(buildout_dir, 'var', 'backups'))
        options.setdefault('location', backup_dir)

    def install(self):
        """Installer"""
        backup_dir = os.path.abspath(self.options['location'])
        if not os.path.isdir(backup_dir):
            os.makedirs(backup_dir)
            logger.info('Created %s', backup_dir)

        #scripts = zc.buildout.easy_install.scripts(
        #    ['backup'], ws, sys.executable, bindir)


        # Return files that were created by the recipe. The buildout
        # will remove all returned files upon reinstall.
        return tuple()

    def update(self):
        """Updater"""
        pass
