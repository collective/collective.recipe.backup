Easy zope backup/restore recipe for buildout
********************************************

.. contents::

``bin/repozo`` is a zope script to make backups of your Data.fs. Looking up
the settings can be a chore. And you have to pick a directory where to put the
backups. This recipe provides **sensible defaults** for your common backup
tasks. Making backups a piece of cake is important!

- bin/backup makes a backup.

- bin/restore restores the latest backup.

- bin/snapshotbackup makes a full backup, separate from the regular
  backups. Handy for copying the current production database to your laptop or
  right before a big change in the site.

Some extra information:

- Code repository: https://svn.plone.org/svn/collective/buildout/collective.recipe.backup
- Questions and comments to mailto:reinout@vanrees.org


.. _instancemanager: http://plone.org/products/instance-manager
