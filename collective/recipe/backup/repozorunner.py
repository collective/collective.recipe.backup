# Wrapper that invokes repozo.
import os

def main(bindir):
    repozo = os.path.join(bindir, 'repozo')
    os.system(repozo)


def backup(conf=None,
           sourceDatafs=None,
           targetDir=None,
           full=False,
           ):
    # if the backup directory doesn't exist, create it.
    if not os.path.exists(targetDir):
        log.info("%s does not exist, creating it now.",
                 targetDir)
        os.makedirs(targetDir)
    arguments = []
    arguments.append('--backup')
    arguments.append('--file=%s' % sourceDatafs)
    arguments.append('--repository=%s' % targetDir)
    if full:
        arguments.append('--full')
        # By default, there's an incremental backup, if possible.
    python = conf.configData['python']
    repozo = os.path.join(conf.zopeDir(), 'bin', 'repozo.py' )
    # Make sure our software home is in the PYTHONPATH
    env={}
    env['PYTHONPATH'] = "%s/lib/python" % conf.zopeDir()
    os.environ.update(env)
    command = ' '.join([python, repozo] + arguments)
    log.info("Backing up database file: %s to %s",
             sourceDatafs, targetDir)
    log.debug("Command used: %s", command)
    os.system(command)
    # We want to clean up old backups automaticly.
    # The number_of_backups var tells us how many full backups we want
    # to keep.
    log.debug("Trying to clean up old backups.")
    filenames = os.listdir(targetDir)
    log.debug("Looked up filenames in the target dir: %s found. %r.",
              len(filenames), filenames)
    num_backups = conf.numberOfBackups()
    log.debug("Max number of backups: %s.", num_backups)
    files_modtimes = []
    for filename in filenames:
        mod_time = os.path.getmtime(os.path.join(targetDir, filename))
        file_ = (filename, mod_time)
        files_modtimes.append(file_)
    # we are only interested in full backups
    fullbackups = [f for f in files_modtimes if f[0].endswith('.fs')]
    log.debug("Filtered out full backups (*.fs): %r.",
              [f[0] for f in fullbackups])
    if len(fullbackups) > num_backups and num_backups != 0:
        log.debug("There are older backups that we can remove.")
        fullbackups = sorted(fullbackups, key=itemgetter(1))
        fullbackups.reverse()
        log.debug("Full backups, sorted by date, newest first: %r.",
                  [f[0] for f in fullbackups])
        oldest_backup_to_keep = fullbackups[(num_backups-1)]
        log.debug("Oldest backup to keep: %s", oldest_backup_to_keep[0])
        last_date_to_keep = oldest_backup_to_keep[1]
        log.debug("The oldest backup we get to keep is from %s.",
                  last_date_to_keep)
        for filename, modtime in files_modtimes:
            if modtime < last_date_to_keep:
                filepath = os.path.join(targetDir, filename)
                os.remove(filepath)
                log.debug("Deleted %s.", filepath)
        log.info("Removed old backups, the latest %s full backups have "
                 "been kept.", str(num_backups))
    else:
        log.debug("Not removing backups.")
        if len(fullbackups) <= num_backups:
            log.debug("Reason: #backups (%s) <= than max (%s).",
                      len(fullbackups), num_backups)
        if num_backups == 0:
            log.debug("Reason: max # of backups is 0, so that is a "
                      "sign to us to not remove backups.")


def restore(conf=None,
            sourceDir=None,
            fromTime=None,
            ):
    # Lets make sure zope is stopped
    useZeo = conf.configData['use_zeo']
    if useZeo:
        runZopectl(conf, 'stop')
        runZeoctl(conf, 'stop')
    else:
        runZopectl(conf, 'stop')
    targetDatafs = conf.databasePath()
    arguments = []
    arguments.append('--recover')
    arguments.append('--output=%s' % targetDatafs)
    arguments.append('--repository=%s' % sourceDir)
    if fromTime:
        arguments.append('--date=%s' % fromTime)
    # Now we have to remove the temp files, if they exist
    for fileName in config.DATABASE_TEMPFILES:
        file = os.path.join(conf.databaseBaseDir(), fileName)
        if os.path.exists(file):
            log.debug("Removing temporary database file: %s" % file)
            os.remove(file)
    python = conf.configData['python']
    repozo = os.path.join(conf.zopeDir(), 'bin','repozo.py' )
    # make sure our software home is in the PYTHONPATH
    env={}
    env['PYTHONPATH']="%s/lib/python" % conf.zopeDir()
    os.environ.update(env)
    command = ' '.join([python, repozo] + arguments)
    log.info("Restoring database file %s from %s.",
             targetDatafs, sourceDir)
    log.debug("Command used: %s",
              command)
    os.system(command)
