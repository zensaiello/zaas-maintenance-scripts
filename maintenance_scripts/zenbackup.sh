#!/bin/bash

if [ -z "${topSD}" ] ; then 
    sd=$(echo "$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )")
    source ${sd}/../setScriptEnv.sh
fi 
if [ ! -f "${apiSD}/zenApiCli.py" ]; then
    echo "Unable to find '${apiSD}/zenApiCli.py'. Script will exit."
    exit
fi

COMPONENT="zenbackup"

# Before we take a backup, remove any automated snapshots.
# This is due to backups locking the DFS, which restricts
# you from managing snapshots during the backup process.
# You don't want a snapshot growing out of control and 
# then not being able to get yourself out of a scary situation.
for snapshot in $(serviced snapshot list -t | grep "Zenoss automated snapshot" |  awk '{print $1}'); do
    serviced snapshot rm "$snapshot"
done

# Run backup
UUID=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="${COMPONENT} has started.",component="${COMPONENT}",device="${DEVICE}",severity=2,evclass="/Cmd",evclasskey=""  -x uuid | cut -d":" -f2)
OUTPUT=$(/usr/bin/serviced backup /opt/serviced/var/backups)
rCode=$?
sleep 5

EVT=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="${COMPONENT} job has completed",component="${COMPONENT}",device="${DEVICE}",severity=0,evclass="/Cmd",evclasskey="${UUID}")
# Validation: backup command exit code
if [ $rCode -eq 0 ] ; then
    SIZE=$(du -k "${SERVICED_BACKUPS_PATH}/${OUTPUT}" | cut -f1)
else
    EVT=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="${COMPONENT} job has failed",message="Output: ${OUTPUT}",component="${COMPONENT}",device="${DEVICE}",severity=4,evclass="/Cmd",evclasskey="${UUID}")
    exit 1
fi
# Validation: backup exists and is larger than 0B
if [ ! -f "${SERVICED_BACKUPS_PATH}/${BACKUP}" ] && [ ! "$SIZE" -gt 0 ]; then
    EVT=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="${COMPONENT} job has failed",message="Output: ${OUTPUT}",component="${COMPONENT}",device="${DEVICE}",severity=4,evclass="/Cmd",evclasskey="${UUID}")
    exit 1
fi
