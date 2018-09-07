from OpenSSL import SSL

from twisted.internet.ssl import ClientContextFactory
from twisted.web.client import HTTPClientFactory, _makeGetterFactory

ClientContextFactory.method = SSL.SSLv23_METHOD

BASE_URL = "https://api.github.com"


class _HTTPClientFactory(HTTPClientFactory):
    def page(self, page):
        if self.waiting:
            self.waiting = 0
            self.deferred.callback((self.response_headers, page))


def getPage(method, url, accessToken=None):
    headers = {}
    if accessToken is not None:
        headers["Authorization"] = "token {0}".format(accessToken)
    factory = _makeGetterFactory(url, _HTTPClientFactory, headers=headers, method=method)
    return factory.deferred


if __name__ == "__main__":
    import sys
    from pprint import pprint as pp
    from twisted.internet import reactor

    def cb(result):
        headers, body = result
        pp(headers)
        reactor.stop()
    user = sys.argv[1]
    d = getPage("GET", "https://api.github.com/users/{0}/repos".format(user))
    d.addBoth(cb)
    reactor.run()
