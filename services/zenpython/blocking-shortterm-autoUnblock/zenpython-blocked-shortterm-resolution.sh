#!/bin/bash

#How long to wait to clear block after the zenpython.blocked is created.
blockWait=30
apiOn=0
if [ -e './json_api.sh' ]; then
   apiOn=1
   . ./json_api.sh
   #Option to override Zenoss Instance details set in the json_api.sh 
   #ZENOSS_URL="https://zenoss5.<your FQDN>"
   #ZENOSS_USERNAME="admin"
   #ZENOSS_PASSWORD="zenoss"
   evtResource="localhost"
fi
#set variables
blkIDs=""
scriptName=`basename $0 | sed 's/\.sh//g'`
tStmp=`date +%s`
zenPyBlkFileName=`echo "${scriptName}-${tStmp}.log" | tr "/" "_"`
#get a list of zenpython instances
svcIDs=$(serviced service status --show-fields 'Name,ServiceID,Status' | grep zenpython | grep "Running" | awk '{print $1, $2}' | sed 's/^.*zenpython//g' | awk '{print $2$1}' 2>/dev/null) 
if [ -z "$svcIDs" ] ; then
   echo "ERROR: 'serviced service status' getting zenpython serviceIDs"
   exit 1
fi
#loop through zenpython instances
for svcID in $svcIDs ; do
   #get contents of zenpython.block file, when size > 0 and over 30 minutes old.
   whatsBlocked=`serviced service attach ${svcID} "/bin/find /var/zenoss/zenpython.blocked -mmin +${blockWait} -and ! -size 0 -exec /usr/bin/cat \{\} \; 2>/dev/null" 2>/dev/null | tr -d $'\r' `
   if [ ! -z "$whatsBlocked" ] ; then
      #Build a list of serviceIDs of zenpythons that are blocked. The assumption some could and others could not be. Likely this would never happen.
      blkIDs="${svcID}
${blkIDs}"
      #'log' info that things are blocked, ideally an event, but need the json_api.sh script to be present.
      if [ $apiOn -eq 0 ] ; then
         printf "BLOCKED: ${svcID}\n$whatsBlocked\n"
      else
         zenoss_api evconsole_router EventsRouter add_event \
            "{\"device\": \"$evtResource\", \
              \"summary\": \"zenpython instance blocked: $svcID\", \
              \"component\": \"zenpython\", \
              \"severity\": \"Error\", \
              \"evclasskey\": \"zenpython-blocked\", \
              \"evclass\": \"/App/Zenoss\", \
              \"message\": \"The datasource(s) blocked are: $whatsBlocked\"}" &> /dev/null

      fi
   fi
done
#loop through all zenpython blocked instances
for psvcID in `echo "$blkIDs" | cut -d"/" -f1 | sort -u` ; do
      for svcID in `echo "${blkIDs}" | grep "$psvcID"` ; do
         #Collect zenpython.log data that may be useful to tracking down the blocking cause
         echo "${svcID}:zenpython.log:blocked" >> ${zenPyBlkFileName}
         serviced service attach ${svcID} grep -v " INFO " /opt/zenoss/log/zenpython.log >> ${zenPyBlkFileName} 2>/dev/null
         #null out zenpython.block file, i.e. unblocking
         serviced service attach ${svcID} su - zenoss -c \"/usr/bin/dd if=/dev/null of=/var/zenoss/zenpython.blocked 2\>/dev/null\" 2>/dev/null
      done
      #Restart zenpython for unblocking to take effect
      serviced service restart ${svcID} 
done
#clear Events
if [ ! -z "$blkIDs" ] ; then
   #Sorry on the use of python in bash, no easy way to parse json in bash.
   evids=`zenoss_api evconsole_router EventsRouter query '{"params":{"eventState":[0,1],"severity":[5,4,3,2],"summary":"datasource has been disabled*","agent":"zenpython*"},"keys":["evid"],"limit":1000}' | python -c 'import sys, json
print(map(lambda x: str(x["evid"]), json.load(sys.stdin)["result"]["events"]))'`
   #JSON API does not seem to like single quotes
   evids=`echo "$evids" | tr "'" '"'`
   #If returned event query is not empty, close events.
   if [ "$evids" != "[]" ] ; then
      zenoss_api evconsole_router EventsRouter close "{\"evids\": $evids}" &> /dev/null
   fi
fi
