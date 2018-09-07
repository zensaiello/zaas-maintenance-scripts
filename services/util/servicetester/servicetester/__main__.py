import sys
import re
import os.path
from pprint import pprint as pp

import Globals

from Products.ZenUtils.ZCmdBase import ZCmdBase
from Products.ZenUtils.Utils import importClass


class ServiceTester(ZCmdBase):
    def run(self):
        service = self.options.service
        if not service:
            raise RuntimeError("You must specify a service")

        try:
            cls = importClass(service)
        except ImportError:
            path = os.path.abspath(service)
            if os.path.isfile(service):
                dir_ = os.path.dirname(path)
                sys.path.append(dir_)
                name = re.findall(r"/?([A-Za-z]+[A-Za-z0-9])*\.", service)[0]
                cls = importClass(name)

        service = cls(self.dmd, "localhost")
        method = getattr(service, self.options.method)
        results = method(self.args)

        for result in results:
            pp(vars(result))

    def buildOptions(self):
        super(ServiceTester, self).buildOptions()
        self.parser.add_option("-s", "--service",
            help="Script path or package.module.class of service")
        self.parser.add_option("-m", "--method", default="remote_getDeviceConfigs",
            help="Method to call")

if __name__ == "__main__":
    serviceTester = ServiceTester()
    serviceTester.run()
