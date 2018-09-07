import json
import re
import urllib
import os.path
import tempfile

import urlparse

from twisted.internet.defer import DeferredList
from twisted.web import resource
from twisted.web.server import NOT_DONE_YET
from twisted.python import failure

from .session import SessionManager
from .githubclient import getPage
from .builder import ZenPackDocBuilder

COOKIE_ID = "__docbuild__"
GITHUB_ACCESS_TOKEN_KEY = "__github_access_token__"
GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize?client_id={0}&scope=repo"
GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token?" \
    "client_id={0}&" \
    "client_secret={1}&" \
    "code={2}"
GITHUB_CONTENTS_URL = "https://raw.githubusercontent.com/zenoss/{0}/{1}/{2}"
BASE_PATH = os.path.dirname(os.path.realpath(__file__))
STATIC_PATH = os.path.join(BASE_PATH, "static")
MIME_TYPES = {
    "html": "text/html",
    "pem": "application/x-pem-file",
    "tgz": "application/tar+gzip",
    "css": "text/css",
    "png": "image/png",
}


class ZenossDocbuild(resource.Resource):
    isLeaf = True

    def __init__(self, sessionPath, githubClientId, githubClientSecret):
        resource.Resource.__init__(self)
        self.githubClientId = githubClientId
        self.githubClientSecret = githubClientSecret
        self.sessions = SessionManager(COOKIE_ID, sessionPath)

    def render_GET(self, request):
        try:
            if request.path != "/login" and self.sessions.get(request, GITHUB_ACCESS_TOKEN_KEY) is None:
                return self.authorize(request)

            base = request.path.split("/")[1]
            try:
                fn = self.PATHS[base]
            except KeyError:
                return self._notFound(request)
            return fn(self, request)
        finally:
            self.sessions.sync()

    def authorize(self, request):
        url = GITHUB_AUTHORIZE_URL.format(self.githubClientId)
        return redirect(url, request)

    def login(self, request):
        query = urlparse.parse_qs(urlparse.urlparse(request.uri).query)
        code = query["code"][0]
        url = GITHUB_ACCESS_TOKEN_URL.format(
            self.githubClientId,
            self.githubClientSecret,
            code,
        )
        d = getPage("POST", url)
        d.addCallback(self._loggedin, request)
        d.addErrback(self._error, request)
        return NOT_DONE_YET

    def _loggedin(self, result, request):
        headers, body = result
        qs = urlparse.parse_qs(body)
        accessToken = qs["access_token"][0]
        self.sessions.set(request, GITHUB_ACCESS_TOKEN_KEY, accessToken)
        return redirect("/", request)

    def getRepos(self, request):
        urlparts = urlparse.urlparse(request.uri)
        qs = urlparse.parse_qs(urlparts.query)
        query = qs["query"][0]
        query += " ZenPacks."
        qs = urllib.urlencode({"q": query})
        d = getPage(
            "GET",
            "?".join(("https://api.github.com/search/repositories", qs)),
            self.sessions.get(request, GITHUB_ACCESS_TOKEN_KEY),
        )
        repos = []
        d.addCallback(self._gotRepos, request, repos)
        d.addErrback(self._error, request)
        return NOT_DONE_YET

    def _error(self, result, request):
        self.sessions.set(request, GITHUB_ACCESS_TOKEN_KEY, None)
        if hasattr(result.value, 'status'):
            request.setResponseCode(int(result.value.status))
            request.write(result.value.response)
        else:
            request.setResponseCode(400)
            request.write("Empty result cannot determine status or response."
                          " Check ZENOSS_DOCBUILD_GITHUB_CLIENT_SECRET in /etc/zenoss-docbuild.conf")
        request.finish()

    def _gotRepos(self, result, request, repos):
        headers, body = result
        for repo in json.loads(body)["items"]:
            if repo["owner"]["login"] == "zenoss":
                repos.append(repo["name"])

        linkHeaders = headers.get("link", [])
        for linkHeader in linkHeaders:
            for link in linkHeader.split(", "):
                url, rel = re.search(r"<(.+)>; rel=\"(.+)\"", link).groups()
                if rel == "next":
                    d = getPage(
                        "GET",
                        url,
                        self.sessions.get(request, GITHUB_ACCESS_TOKEN_KEY),
                    )
                    d.addBoth(self._gotRepos, request, repos)
                    return NOT_DONE_YET

        repos.sort()
        request.setHeader("Content-Type", "application/json")
        request.write(json.dumps(repos))
        request.finish()

    def build(self, request):
        urlparts = urlparse.urlparse(request.uri)
        qs = urlparse.parse_qs(urlparts.query)
        repo = qs["repo"][0]
        branch = qs["branch"][0]

        builder = ZenPackDocBuilder(repo)
        url = GITHUB_CONTENTS_URL.format(
                repo,
                branch,
                "doc.yaml",
            )
        d = getPage(
                    "GET",
                    url,
                    self.sessions.get(request, GITHUB_ACCESS_TOKEN_KEY),
                    )
        d.addBoth(self._runProcessors, builder, repo, branch, request)
        return NOT_DONE_YET

    def _runProcessors(self, result, builder, repo, branch, request):
        try:
            if not isinstance(result, failure.Failure):
                headers, body = result
                builder.buildProcessorsFromDocYaml(body, 'default')
        except Exception as e:
            # Either doesn't exist or failed to load, ignore and use default files
            pass

        deferreds = []
        for path, fn in builder.getProcessors():
            url = GITHUB_CONTENTS_URL.format(
                repo,
                branch,
                path,
            )
            d = getPage(
                "GET",
                url,
                self.sessions.get(request, GITHUB_ACCESS_TOKEN_KEY),
            )
            d.addBoth(fn)
            deferreds.append(d)
        dl = DeferredList(deferreds)
        dl.addCallback(self._gotBuild, builder, repo, request)

        return NOT_DONE_YET

    def _gotBuild(self, result, builder, repo, request):

        if builder.nothingFound():
            request.setResponseCode(404)
            request.write("Need at least 1 file to generate a doc and none found")
            request.finish()
            return

        urlparts = urlparse.urlparse(request.uri)
        qs = urlparse.parse_qs(urlparts.query)
        fileformat = qs["fileformat"][0]
        ext = ".odt"
        if fileformat in ("odt", "docx", "pdf"):
            ext = "." + fileformat
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as fh:
                try:
                    builder.generatePanDocFile(fileformat,
                                               fh.name)
                    with open(fh.name, mode='rb') as file:  # b is important -> binary
                        output = file.read()
                except Exception as e:
                    request.setResponseCode(500)
                    request.write(e)
                    request.finish()
                    return
                finally:
                    os.remove(fh.name)
        else:
            # default
            ext = ".odt"
            try:
                output = builder.generateDoc("odt")
            except Exception as e:
                request.setResponseCode(500)
                request.write(e)
                request.finish()
                return

        request.responseHeaders.addRawHeader(
            "Content-Type", "application/octet-stream")
        request.responseHeaders.addRawHeader(
            "Content-Disposition",
            "attachment; filename={0}{1}".format(repo, ext),
        )
        request.responseHeaders.addRawHeader("Content-Transfer-Encoding", "binary")
        request.write(output)
        request.finish()

    def getIndex(self, request):
        return self._getStatic(request, "index.html")

    def getStatic(self, request):
        filename = request.path.split("/")[-1]
        return self._getStatic(request, filename)

    def _getStatic(self, request, filename):
        path = os.path.join(STATIC_PATH, filename)
        if os.path.exists(path):
            request.responseHeaders.addRawHeader(
                "Content-Type", MIME_TYPES[filename.split(".")[-1]])
            with open(path, "rb") as fh:
                return fh.read()
        else:
            return self._notFound(request)

    def _notFound(self, request):
        request.setResponseCode(404)
        return "Not found"

    PATHS = {
        "static": getStatic,
        "login": login,
        "getRepos": getRepos,
        "build": build,
        "authorize": authorize,
        "": getIndex,
    }


def redirect(url, request):
    request.redirect(url)
    request.finish()
    return NOT_DONE_YET
