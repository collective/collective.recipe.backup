# Small utility methods.
from collective.recipe.backup import config

import logging
import os
import shutil
import subprocess
import sys


try:
    from builtins import input as raw_input
except ImportError:
    # Python 2 has raw_input available by default.
    pass


logger = logging.getLogger("utils")

# For zc.buildout's system() method:
MUST_CLOSE_FDS = not sys.platform.startswith("win")

try:
    # Python 2
    stringtypes = basestring
except NameError:
    # Python 3
    stringtypes = str


def system(command, input=""):
    """commands.getoutput() replacement that also works on windows

    This was copied from zest.releaser.
    """
    p = subprocess.Popen(
        command,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=MUST_CLOSE_FDS,
    )
    i, o, e = (p.stdin, p.stdout, p.stderr)
    if input:
        i.write(input)
    i.close()
    result = o.read() + e.read()
    o.close()
    e.close()
    # Return the result plus a return value (0: all is fine)
    return result, p.wait()


def ask(question, default=True, exact=False):
    """Ask the question in y/n form and return True/False.

    If you don't want a default 'yes', set default to None (or to False if you
    want a default 'no').

    With exact=True, we want to get a literal 'yes' or 'no', at least
    when it does not match the default.

    """
    while True:
        yn = "y/n"
        if exact:
            yn = "yes/no"
        if default is True:
            yn = yn.replace("y", "Y")
        if default is False:
            yn = yn.replace("n", "N")
        q = f"{question} ({yn})? "
        input = raw_input(q)
        if input:
            answer = input
        else:
            answer = ""
        if not answer and default is not None:
            return default
        if exact and answer.lower() not in ("yes", "no"):
            print("Please explicitly answer yes/no in full " "(or accept the default)")
            continue
        if answer:
            answer = answer[0].lower()
            if answer == "y":
                return True
            if answer == "n":
                return False
        # We really want an answer.
        print("Please explicitly answer y/n")
        continue


def execute_or_fail(command):
    if not command:
        return
    output, failed = system(command)
    logger.debug("command executed: %r", command)
    if output:
        print(output)
    if failed:
        logger.error("command %r failed. See message above.", command)
        sys.exit(1)


def check_folders(
    storages, backup_blobs=True, only_blobs=False, backup_method=config.STANDARD_BACKUP
):
    """Check that folders exist, and create them if not."""
    backup = backup_method == config.STANDARD_BACKUP
    snapshot = backup_method == config.SNAPSHOT_BACKUP
    zipbackup = backup_method == config.ZIP_BACKUP
    for storage in storages:
        pathdirs = []
        if not only_blobs:
            if backup:
                pathdirs.append(storage.get("backup_location"))
            if snapshot:
                pathdirs.append(storage.get("snapshot_location"))
            if zipbackup:
                pathdirs.append(storage.get("zip_location"))
        if backup_blobs:
            if backup:
                pathdirs.append(storage.get("blob_backup_location"))
            if snapshot:
                pathdirs.append(storage.get("blob_snapshot_location"))
            if zipbackup:
                pathdirs.append(storage.get("blob_zip_location"))

        for pathdir in pathdirs:
            if pathdir and not os.path.isdir(pathdir):
                os.makedirs(pathdir)
                logger.info("Created %s", pathdir)


def try_create_folder(pathdir):
    """Try to create a folder, but remove it again.

    >>> try_create_folder('mytest')
    >>> mkdir('mytest')
    >>> mkdir('mytest', 'keep')
    >>> write('mytest', 'myfile', 'I am a file.')
    >>> ls('mytest')
    d  keep
    -   myfile
    >>> try_create_folder('mytest')
    >>> ls('mytest')
    d  keep
    -   myfile
    >>> try_create_folder('mytest/folder')
    >>> ls('mytest')
    d  keep
    -   myfile
    >>> try_create_folder('mytest/keep')
    >>> ls('mytest')
    d  keep
    -   myfile
    >>> try_create_folder('mytest/folder/sub')
    >>> ls('mytest')
    d  keep
    -   myfile
    >>> try_create_folder('mytest/keep/sub')
    >>> ls('mytest')
    d  keep
    -   myfile
    >>> remove('mytest')

    """
    if not pathdir:
        return
    if os.path.exists(pathdir):
        if not os.path.isdir(pathdir):
            logger.warning("WARNING: %s is a file, not a directory.", pathdir)
        return
    # Now the tricky thing is: if only a/ exists, without sub
    # directories, and we call this function with a/b/c, we do not
    # want to have a directory a/b/ left over at the end.
    if os.path.isabs(pathdir):
        newdir = os.path.sep
    else:
        newdir = os.getcwd()
    parts = pathdir.split(os.path.sep)
    # Find the first part that does not exist.
    for part in parts:
        newdir = os.path.join(newdir, part)
        if os.path.exists(newdir):
            if not os.path.isdir(newdir):
                logger.warning("WARNING: %s is a file, not a directory.", newdir)
                return
            continue
        # newdir does not exist.  Try to create the full path, and the
        # remove newdir.
        try:
            os.makedirs(pathdir)
            shutil.rmtree(newdir)
        except OSError:
            logger.warning("WARNING: Not able to create %s", pathdir)
        return


def get_date_from_args():
    # Try to find a date in the command line arguments
    date = None
    for arg in sys.argv:
        if arg in ("-q", "-n", "--quiet", "--no-prompt"):
            continue
        if arg.find("restore") != -1:
            continue

        # We can assume this argument is a date
        date = arg
        logger.debug(
            "Argument passed to bin/restore, we assume it is "
            "a date that we have to pass to repozo: %s.",
            date,
        )
        logger.info("Date restriction: restoring state at %s.", date)
        break
    return date
