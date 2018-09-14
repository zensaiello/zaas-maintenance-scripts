#!/bin/env python
import zenApiLib
import sys
import os
from urlparse import urlparse
from datetime import date


def write2File(sType, sUid, sData):
    '''
    Write transform text to a file
    '''
    exportPath = '{}/export_{}_{}'.format(
        os.environ['topSD'],
        zenInstance,
        date.today()
    )
    if not os.path.exists(exportPath):
        os.makedirs(exportPath)
    sFilePath = "{}/{}.{}.txt".format(
        exportPath,
        sUid,
        sType
    )
    print "INFO: writing {}".format(
        sFilePath
    )
    try:
        oFile = open(sFilePath, 'w')
        oFile.write(sData)
        oFile.close()
    except Exception, e:
        print "ERROR: %s" % (e)
        sys.exit(1)


if __name__ == '__main__':
    api = zenApiLib.zenConnector(routerName = 'EventClassesRouter')
    api.config['timeout'] = 600
    zenInstance = urlparse(api.config['url']).hostname
    jobName="zenbatchdump"
    api.setRouter('EventsRouter')
    api.callMethod(
        'add_event',
        summary="{} job has started.".format(jobName),
        component=jobName,
        device=os.environ['DEVICE'],
        severity=2,
        evclass="/Cmd",
        evclasskey=""
    )
    api.setRouter('DeviceDumpLoadRouter')
    apiResult = api.callMethod('exportDevices')
    api.setRouter('EventsRouter')
    api.callMethod(
        'add_event',
        summary="{} job completed.".format(jobName),
        component=jobName,
        device=os.environ['DEVICE'],
        severity=0,
        evclass="/Cmd",
        evclasskey=""
    )
    if apiResult['result']['success']:
        write2File('devices', 'batchDump', apiResult['result']['data'])
    else:
        api.callMethod(
            'add_event',
            summary="{} job has failed.".format(jobName),
            message="Results: {}".format(apiResult['msg']),
            component=jobName,
            device=os.environ['DEVICE'],
            severity=4,
            evclass="/Cmd",
            evclasskey=""
        )
