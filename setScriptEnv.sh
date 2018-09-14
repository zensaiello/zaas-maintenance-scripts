#
export topSD=`echo "$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"`
export zaasSD="${topSD}/maintenance_scripts"
export svcsSD="${topSD}/services"
export apiSD="${topSD}/zenoss-RM-api"
#
if [ -z "$PYTHONPATH" ] ; then
    export PYTHONPATH="${apiSD}"
else
     export PYTHONPATH="${PYTHONPAT}:${apiSD}"
fi
# Set the backup path base on /etc/default/serviced override/default
export SERVICED_BACKUPS_PATH=$(grep "^SERVICED_BACKUPS_PATH" /etc/default/serviced | sed 's/^.*=//')
if [ -z "$SERVICED_BACKUPS_PATH" ]; then
   export SERVICED_BACKUPS_PATH=$(grep "^#.*SERVICED_BACKUPS_PATH" /etc/default/serviced | sed 's/^.*=//')
fi
#
export DOCKER_SRC_DIR="/mnt/pwd"
export IPADDR=$(hostname -i)
export TARGET=$(hostname -s)
export DEVICE=$("${apiSD}/zenApiCli.py" -r DeviceRouter -m getDevices -d keys="['name','ipAddress']",params="{'ipAddress': '${IPADDR}'}" -x result.devices.0.name | cut -d":" -f2)
