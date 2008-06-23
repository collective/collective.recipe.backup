# Wrapper that invokes repozo.
import os

def main(bindir):
    repozo = os.path.join(bindir, 'repozo')
    os.system(repozo)
