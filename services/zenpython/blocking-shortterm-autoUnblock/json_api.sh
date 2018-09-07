#!/bin/sh

# Script taken from http://wiki.zenoss.org/Working_with_the_JSON_API which says:
# This page was last modified on 14 June 2016, at 13:55

# Your Zenoss server settings.
# The URL to access your Zenoss5 Endpoint
ZENOSS_URL="https://zenoss5.<your FQDN>"
ZENOSS_USERNAME="admin"
ZENOSS_PASSWORD="zenoss"

# Generic call to make Zenoss JSON API calls easier on the shell.
zenoss_api () {
    ROUTER_ENDPOINT=$1
    ROUTER_ACTION=$2
    ROUTER_METHOD=$3
    DATA=$4

    if [ -z "${DATA}" ]; then
        echo "Usage: zenoss_api <endpoint> <action> <method> <data>"
        return 1
    fi
# add a -k for the curl call to ignore the default cert
    curl \
        -s \
        -k \
        -u "$ZENOSS_USERNAME:$ZENOSS_PASSWORD" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{\"action\":\"$ROUTER_ACTION\",\"method\":\"$ROUTER_METHOD\",\"data\":[$DATA], \"tid\":1}" \
        "$ZENOSS_URL/zport/dmd/$ROUTER_ENDPOINT"
}

# Helper call to send an event.
#
# Example usage:
#   zenoss_send_event device1 component1 5 key1 test
zenoss_send_event() {
    DEVICE=$1
    COMPONENT=$2
    SEVERITY=$3
    EVENT_CLASS_KEY=$4
    SUMMARY=$5

    if [ -z "$SUMMARY" ]; then
        echo "Usage: zenoss_send_event <device> <component> <severity> <eventClassKey> <summary>"
        return 1
    fi

    zenoss_api evconsole_router EventsRouter add_event \
        "{\"device\":\"$DEVICE\",\"summary\":\"$SUMMARY\",\"component\":\"$COMPONENT\",\"severity\":\"$SEVERITY\",\"evclasskey\":\"$EVENT_CLASS_KEY\"}"
}

# Helper call for adding standard device types.
zenoss_add_device() {
    DEVICE_HOSTNAME=$1
    DEVICE_CLASS=$2

    if [ -z "$DEVICE_CLASS" ]; then
        echo "Usage: zenoss_add_device <host> <device class>"
        return 1
    fi

    zenoss_api device_router DeviceRouter addDevice "{\"deviceName\":\"$DEVICE_HOSTNAME\",\"deviceClass\":\"$DEVICE_CLASS\",\"collector\":\"localhost\",\"model\":true,\"title\":\"\",\"productionState\":\"1000\",\"priority\":\"3\",\"snmpCommunity\":\"\",\"snmpPort\":161,\"tag\":\"\",\"rackSlot\":\"\",\"serialNumber\":\"\",\"hwManufacturer\":\"\",\"hwProductName\":\"\",\"osManufacturer\":\"\",\"osProductName\":\"\",\"comments\":\"\"}"
}

