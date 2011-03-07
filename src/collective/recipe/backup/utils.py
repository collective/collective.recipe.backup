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
    return result
