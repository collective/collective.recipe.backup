# Small utility methods.
import logging
import subprocess
import sys

logger = logging.getLogger('utils')

# For zc.buildout's system() method:
MUST_CLOSE_FDS = not sys.platform.startswith('win')


def system(command, input=''):
    """commands.getoutput() replacement that also works on windows

    This was copied from zest.releaser.
    """
    p = subprocess.Popen(command,
                         shell=True,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         close_fds=MUST_CLOSE_FDS)
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
        yn = 'y/n'
        if exact:
            yn = 'yes/no'
        if default is True:
            yn = yn.replace('y', 'Y')
        if default is False:
            yn = yn.replace('n', 'N')
        q = question + " (%s)? " % yn
        input = raw_input(q)
        if input:
            answer = input
        else:
            answer = ''
        if not answer and default is not None:
            return default
        if exact and answer.lower() not in ('yes', 'no'):
            print ("Please explicitly answer yes/no in full "
                   "(or accept the default)")
            continue
        if answer:
            answer = answer[0].lower()
            if answer == 'y':
                return True
            if answer == 'n':
                return False
        # We really want an answer.
        print 'Please explicitly answer y/n'
        continue


def execute_or_fail(command):
    if not command:
        return
    output, failed = system(command)
    logger.debug("command executed: %r", command)
    if output:
        print output
    if failed:
        logger.error("command %r failed. See message above.", command)
        sys.exit(1)
