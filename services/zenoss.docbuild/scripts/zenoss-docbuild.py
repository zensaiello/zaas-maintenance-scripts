#!/usr/bin/env python

import sys

from twisted.internet import reactor
from twisted.web import server

from zenoss.docbuild.webserver import ZenossDocbuild


def main(host, port, sessionPath, githubClientId, githubClientSecret):
    port = int(port)
    resource = ZenossDocbuild(sessionPath, githubClientId, githubClientSecret)
    site = server.Site(resource)
    reactor.listenTCP(port, site, interface=host)
    reactor.run()

if __name__ == "__main__":
    main(*sys.argv[1:])

