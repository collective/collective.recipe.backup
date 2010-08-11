Easy zope backup/restore recipe for buildout
********************************************

.. contents::


This recipe is a wrapper around the ``bin/repozo`` script in your zope
buildout.  It requires that this script is already made available.  If
this is not the case, you will get an error like this when you run one
of the scripts: ``bin/repozo: No such file or directory``.  You should
be fine when you are on Plone 3 or when you are on Plone 4 and are using
``plone.recipe.zeoserver``.  If this is not the case, the easiest way
of getting a ``bin/repozo`` script is to add a new section in your
buildout.cfg (do not forget to add it in the ``parts`` directive)::

  [repozo]
  recipe = zc.recipe.egg
  eggs = ZODB3
  scripts = repozo


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

- Code repository: http://svn.plone.org/svn/collective/buildout/collective.recipe.backup
- Questions and comments to mailto:reinout@vanrees.org and  mailto:maurits@vanrees.org.

.. ATTENTION::
  If your buildout uses blobstorage to store files (see the
  ``var/blobstorage`` directory, if it exists), those files are
  currently not backed up by this recipe.  You will have to do
  something yourself (create a script that makes a tarball, or
  uses scp or rsync or something like that).  A future version of this
  recipe may deal with this.


.. _instancemanager: http://plone.org/products/instance-manager
