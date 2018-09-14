#!/bin/bash

#
# fstrim
#

if [ -z "${topSD}" ] ; then 
    sd=$(echo "$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )")
    source ${sd}/../setScriptEnv.sh
fi 
if [ ! -f "${apiSD}/zenApiCli.py" ]; then
    echo "Unable to find '${apiSD}/zenApiCli.py'. Script will exit."
    exit
fi

COMPONENT="FSTrim"

UUID=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="${COMPONENT} job has started.",component="${COMPONENT}",device="${DEVICE}",severity=2,evclass="/Cmd",evclasskey=""  -x uuid | cut -d":" -f2)
OUTPUT=$(/usr/sbin/fstrim -av)

sleep 5
CLEAR=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="${COMPONENT} job completed.",message="Results: ${OUTPUT}",component="${COMPONENT}",device="${DEVICE}",severity=0,evclass="/Cmd",evclasskey="${UUID}")
