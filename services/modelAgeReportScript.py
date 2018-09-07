#!/usr/bin/env python

# Note: avoid running this from a shell zope as it will run on the CC master.
# You risk running the system low or out or resources which can kill everything.
# Place the script on the DFS where you will be able to get to it from a running zope
# Output will go to:
# /opt/serviced/var/volumes/VOLUME_ID/var-zenpacks/


import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
from ZODB.transact import transact
from Products.Zuul import getFacade
import time

dmd = ZenScriptBase(connect=True).dmd
zep = getFacade('zep')

f = open('/var/zenoss/devs_by_class_model_times-'+time.strftime("%Y-%m-%d-%H%M%S")+'.csv','w')
l = "Device Class, Device, Last Modeled DateTime, Last Modeled Date, Production State, Model Events, Modeler Timeout Setting \n"
f.write(l)

issues={}
zep_filter = zep.createEventFilter(severity=[5,4],status=[0,1], agent=('zenmodeler'))
modEvents = zep.getEventSummariesGenerator(filter=zep_filter)
for evt in modEvents:
    issues[str(evt['occurrence'][0]['actor']['element_title'])] = str(evt['occurrence'][0]['summary'])

devices = {}
for dev in dmd.Devices.getSubDevices():
    devices[dev.id] = (dev.getDeviceClassName(), dev.getProdState(), dev.getSnmpLastCollection(), issues.get(dev.id, ''), dev.zCollectorClientTimeout)

devclasses = {}
for dev in devices:                    
    dc, prodState, modTime, summary, modTimeout = devices[dev]                                                          
    if not devclasses.get(dc):
        devclasses[dc] = []
    devclasses[dc].append((dev, prodState, modTime, summary, modTimeout))


for dc in devclasses:
    for dev in devclasses[dc]:
        if dev[3] == "":
            lastModelEvent = "No Events"
        else:
            lastModelEvent = dev[3]
        if str(dev[2]) == "1970/01/01 00:00:00 UTC":
            lastModelTime = "Never Modeled"
        else:
            lastModelTime = dev[2]
        lastModelDate = dev[2].strftime('%Y/%m/%d')
        l = dc + "," + dev[0] + "," + str(lastModelTime) + "," + lastModelDate + "," + dev[1] + "," + lastModelEvent + "," + str(dev[4]) + "\n"
        f.write(l)

f.close()
