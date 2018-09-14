#!/usr/bin/env python

# stdlib Imports
import json
from sys import exit
import os
from urlparse import urlparse
import zenApiLib
from datetime import date

zenAPI = zenApiLib.zenConnector(section = 'default')
zenInstance = urlparse(zenAPI.config['url']).hostname


def TriggerRouter(sMethod, dData={}):
    zenAPI.setRouter('TriggersRouter')
    respData = zenAPI.callMethod(sMethod, **dData)
    if not respData['result']['success']:
        print "ERROR: TriggerRouter %s method call non-successful" % sMethod
        print respData
        print "Data submitted was:"
        print response.request.body
        exit(1)
    return respData['result']['data']
    

def write2File(sType, lData):
    exportPath = '{}/export_{}_{}'.format(
        os.environ['topSD'],
        zenInstance,
        date.today()
    )
    if not os.path.exists(exportPath):
        os.makedirs(exportPath)
    for dEntry in lData:
        print "INFO: writing %s/%s.%s.json" % (
            exportPath,
            dEntry['name'],
            sType
        )
        try:
            trigFile = open("%s/%s.%s.json" % (
                exportPath,
                dEntry['name'],
                sType),
                'w'
            )
            trigFile.write(json.dumps(dEntry))
            trigFile.close()
        except Exception, e:
            print "ERROR: %s" % (e)
            exit(1)

if __name__ == "__main__":
    jobName="zenTrigDump"
    zenAPI.setRouter('EventsRouter')
    zenAPI.callMethod(
        'add_event',
        summary="{} job has started.".format(jobName),
        component=jobName,
        device=os.environ['DEVICE'],
        severity=2,
        evclass="/Cmd",
        evclasskey=""
    )
    lTriggers = TriggerRouter('getTriggers')
    write2File('trigger', lTriggers)
    #
    lNotifications = TriggerRouter('getNotifications')
    write2File('notification', lNotifications)
    #
    lNotifWindows = []
    for dNotif in lNotifications:
        lWindows = TriggerRouter('getWindows', dData={'uid': dNotif['uid']})
        lNotifWindows = lNotifWindows + lWindows
    write2File('window', lNotifWindows)
    zenAPI.setRouter('EventsRouter')
    zenAPI.callMethod(
        'add_event',
        summary="{} job completed.".format(jobName),
        component=jobName,
        device=os.environ['DEVICE'],
        severity=0,
        evclass="/Cmd",
        evclasskey=""
    )
