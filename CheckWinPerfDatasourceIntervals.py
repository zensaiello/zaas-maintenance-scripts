#!/usr/bin/env python

import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
from Products.Zuul.interfaces import ICatalogTool
from ZenPacks.zenoss.Microsoft.Windows.datasources.PerfmonDataSource import PerfmonDataSource

dmd = ZenScriptBase(connect=True).dmd
f = open('/var/zenoss/WinPerfDataSourceIssues.txt','w')

results = ICatalogTool(dmd.Devices.Server.Microsoft).search(PerfmonDataSource)
for r in results:
    try:
        ds = r.getObject()
    except Exception:
        continue
    if ds.cycletime != "${here/zWinPerfmonInterval}":
        l = "Issue with template '%s' cycletime is currently set to '%s' should be set to '${here/zWinPerfmonInterval}'" % (ds.getPrimaryId(), ds.cycletime)
        f.write(l)

f.close()
