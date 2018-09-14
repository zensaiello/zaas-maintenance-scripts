#!/bin/bash

#
# Zenoss 5x batch dump
#

if [ -z "${topSD}" ] ; then 
    sd=$(echo "$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )")
    source ${sd}/../setScriptEnv.sh
fi 
if [ ! -f "${apiSD}/zenApiCli.py" ]; then
    echo "Unable to find '${apiSD}/zenApiCli.py'. Script will exit."
    exit
fi

COMPONENT="zenbatchdump"

# Run zenbatchdump
UUID=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="${COMPONENT} job has started.",component="${COMPONENT}",device="${DEVICE}",severity=2,evclass="/Cmd",evclasskey=""  -x uuid | cut -d":" -f2)
FILENAME="zenbatchdump-$(date +\%Y\%m\%d).json"
err=`"${apiSD}/zenApiCli.py" -t 600 -r DeviceDumpLoadRouter -m exportDevices -x result.data 1>"${SERVICED_BACKUPS_PATH}/${FILENAME}"`
rCode=$?

# API zenbatchdump work ?
EVT=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="${COMPONENT} job has completed",component="${COMPONENT}",device="${DEVICE}",severity=0,evclass="/Cmd",evclasskey="${UUID}")
if [ ${rCode} -ne 0 ]; then
    EVT=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="${COMPONENT} job has failed",component="${COMPONENT}",device="${DEVICE}",severity=4,evclass="/Cmd",evclasskey="${UUID}")
fi
