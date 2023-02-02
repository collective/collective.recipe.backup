#!/bin/sh
# Work around tox limitation. Given this command:
#   docker run --user="$(id -u $(whoami)):$(getent group $(whoami)|cut -d: -f3)" --rm -v "{toxinidir}":/github/workspace plone/code-quality:latest format
# You get this error:
#   docker: Error response from daemon: unable to find user $(id -u $(whoami)): no matching entries in passwd file.
docker run --user="$(id -u $(whoami)):$(getent group $(whoami)|cut -d: -f3)" --rm -v "${PWD}":/github/workspace plone/code-quality:latest format
