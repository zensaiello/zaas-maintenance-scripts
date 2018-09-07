import random
import shelve
import string


class SessionManager(object):
    def __init__(self, cookieId, path):
        self._cookieId = cookieId
        self._sessions = shelve.open(path, writeback=True)

    def _getSessionId(self, request):
        cookieHeader = request.getHeader("cookie")
        for cookie in (cookieHeader or "=").split("; "):
            name, value = cookie.split("=")
            if name == self._cookieId:
                cookieId = value
                break
        else:
            cookieId = "".join(
                random.choice(string.ascii_letters) for i in range(20)
            )

        request.setHeader("Set-Cookie", "=".join((self._cookieId, cookieId)))

        return cookieId

    def get(self, request, name):
        cookieId = self._getSessionId(request)
        if cookieId not in self._sessions:
            return

        return self._sessions[cookieId].get(name)

    def set(self, request, name, value):
        cookieId = self._getSessionId(request)
        if cookieId not in self._sessions:
            self._sessions[cookieId] = {}

        session = self._sessions[cookieId]
        session[name] = value
        self._sessions[cookieId] = session

    def sync(self):
        self._sessions.sync()
