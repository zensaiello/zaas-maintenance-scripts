#!/bin/bash

#
# This script executes out of the box toolbox scans
# on either a scheduled or ad hoc basis. 
# Runs toolbox per the standard defined in:
# https://zenoss.atlassian.net/wiki/spaces/RM/pages/608895535/Running+the+toolbox
# If scan still cannot fix, an event will be generated into the
# configured Zenoss instance in zenoss_json.sh as a warning
# event.
#
# This script is to be run on the Control Center master.
# 
# Usage: ./toolboxscans.sh <scan_name>
#

if [ -z "${topSD}" ] ; then 
    sd=$(echo "$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )")
    source ${sd}/../setScriptEnv.sh
fi 

if [[ -z $1 ]]; then
    echo "Usage: ./toolboxscans.sh <scan_name>"
    echo "Example: ./toolboxscans.sh zodbscan"
    exit
fi

# Declare variables
SCAN="$1"
LOG="$SCAN-$(date +%Y%m%d).log"
LOGDIR="/var/log/serviced/toolboxscans"
COMPONENT="toolboxscans"

# Check if toolbox log directory exists. If not, create it
if [[ ! -d $LOGDIR ]]; then
    mkdir $LOGDIR
    chmod 777 $LOGDIR
fi

# Only run this portion if $SCAN = zodbscan
if [[ $SCAN = "zodbscan" ]]; then

    UUID=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="${SCAN} has started.",component="${COMPONENT}",device="${DEVICE}",severity=2,evclass="/Cmd",evclasskey=""  -x uuid | cut -d":" -f2)
	serviced service shell --mount '/var/log/serviced/toolboxscans,/opt/zenoss/log/toolbox' zope su - zenoss -c "yes | $SCAN -s"

    # If the scan fails...
    if [[ "$?" != "0" ]]; then
        CLEAR=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="$SCAN has completed with errors.",component="${COMPONENT}",device="${DEVICE}",severity=0,evclass="/Cmd",evclasskey="${UUID}")
        sleep 
        UUID=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="$SCAN has failed. Running findposkeyerror with -f.",component="${COMPONENT}",device="${DEVICE}",severity=3,evclass="/Cmd",evclasskey=""  -x uuid | cut -d":" -f2)

		mv $LOGDIR/"$SCAN.log" $LOGDIR/"$LOG"		

        SCAN="findposkeyerror"

        serviced service shell --mount '/var/log/serviced/toolboxscans,/opt/zenoss/log/toolbox' zope su - zenoss -c "yes | $SCAN -f"

		# If the scan fails...
        if [[ "$?" != "0" ]]; then
            CLEAR=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="$SCAN completed, with errors.",component="${COMPONENT}",device="${DEVICE}",severity=0,evclass="/Cmd",evclasskey="${UUID}")
            UUID=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="$SCAN has failed. Check /var/log/serviced/toolboxscans for details.",component="${COMPONENT}",device="${DEVICE}",severity=5,evclass="/Cmd",evclasskey=""  -x uuid | cut -d":" -f2)
            mv $LOGDIR/"$SCAN.log" $LOGDIR/"$LOG"
            exit 1

        # If -f resolves the issue...
        else
            clearZenossEvent "$DEVICE" "$COMPONENT" "$SCAN -f fixed all errors for $TARGET." "$UUID"
            CLEAR=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="$SCAN -f fixed all errors",component="${COMPONENT}",device="${DEVICE}",severity=0,evclass="/Cmd",evclasskey="${UUID}")
            mv $LOGDIR/"$SCAN.log" $LOGDIR/"$LOG"
            exit 0
        fi

    # If the scan succeeds...
    else
        CLEAR=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="$SCAN has completed",component="${COMPONENT}",device="${DEVICE}",severity=0,evclass="/Cmd",evclasskey="${UUID}")
        mv $LOGDIR/"$SCAN.log" $LOGDIR/"$LOG"
        exit 0
    fi
fi

# Only run this if $SCAN = zenrelationscan or zencatalogscan
if [[ $SCAN = "zenrelationscan" ]] || [[ $SCAN = "zencatalogscan" ]]; then

    UUID=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="${SCAN} has started.",component="${COMPONENT}",device="${DEVICE}",severity=2,evclass="/Cmd",evclasskey=""  -x uuid | cut -d":" -f2)
    # Why '-s' ?
    serviced service shell --mount '/var/log/serviced/toolboxscans,/opt/zenoss/log/toolbox' zope su - zenoss -c "yes | $SCAN -f -s"

    # If the scan fails...
    if [[ "$?" != "0" ]]; then
        CLEAR=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="$SCAN completed, with errors.",component="${COMPONENT}",device="${DEVICE}",severity=0,evclass="/Cmd",evclasskey="${UUID}")
        UUID=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="$SCAN has failed. Check /var/log/serviced/toolboxscans for details.",component="${COMPONENT}",device="${DEVICE}",severity=5,evclass="/Cmd",evclasskey=""  -x uuid | cut -d":" -f2)
        mv $LOGDIR/"$SCAN.log" $LOGDIR/"$LOG"
        exit 1

    # If the scan succeeds...
    else
        CLEAR=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="$SCAN completed",component="${COMPONENT}",device="${DEVICE}",severity=0,evclass="/Cmd",evclasskey="${UUID}")
        mv $LOGDIR/"$SCAN.log" $LOGDIR/"$LOG"
        exit 0
    fi
fi

# Only run this portion if $SCAN = zenossdbpack
if [[ $SCAN = "zenossdbpack" ]]; then

    UUID=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="${SCAN} has started.",component="${COMPONENT}",device="${DEVICE}",severity=2,evclass="/Cmd",evclasskey=""  -x uuid | cut -d":" -f2)
    serviced service run --mount /var/log/serviced/toolboxscans,/opt/zenoss/log zope zenossdbpack

    # If the scan fails...
    if [[ "$?" != "0" ]]; then
        CLEAR=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="$SCAN completed, with errors.",component="${COMPONENT}",device="${DEVICE}",severity=0,evclass="/Cmd",evclasskey="${UUID}")
        sleep 3
        UUID=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="$SCAN has failed. Check /var/log/serviced/toolboxscans for details.",component="${COMPONENT}",device="${DEVICE}",severity=5,evclass="/Cmd",evclasskey=""  -x uuid | cut -d":" -f2)
        mv $LOGDIR/"$SCAN.log" $LOGDIR/"$LOG"
        exit 1
    
    # If the scan succeeds...
    else
        CLEAR=$("${apiSD}/zenApiCli.py" -r EventsRouter -m add_event -d summary="$SCAN completed",component="${COMPONENT}",device="${DEVICE}",severity=0,evclass="/Cmd",evclasskey="${UUID}")
        mv $LOGDIR/"$SCAN.log" $LOGDIR/"$LOG"
        exit 0
    fi
fi
