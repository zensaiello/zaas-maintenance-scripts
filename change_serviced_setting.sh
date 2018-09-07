#!/bin/sh
#
# Manipulate settings for SERVICED variables
#
CONFIG_FILE="/etc/default/serviced"
FORCE=false
COMMENT=false
REVERT=false
DEBUG=false
# DEBUG=true

# Usage, display and exit
usage() {
   echo "Usage: $0 [-fcr] <SERVICED_VARIABLE> <VALUE_TO_SET>"
   echo "  -f forces overwite of value that is current uncommented"
   echo "  -c forces overwrite of a commented out default value"
   echo "  -r remove uncommented value ie revert to commented out default value"
   exit 1
}

# Parse flags
while getopts 'fcr' flag; do
  case "${flag}" in
    f|c|r) 
		[ ! -z "$FLAG" ] && echo '-f, -c and -r are mutually exclusive. Re-run with at most one.' && usage
                FLAG="${flag}"
                ;;
  esac
done

case "$FLAG" in
    f) FORCE=true ;;
    c) COMMENT=true ;;
    r) REVERT=true ;;
esac


# Parse args
shift $((OPTIND-1)) 

VAR="$1"
VALUE="$2"

if [ "$VAR" == "" ]; then
   usage
# Value u=is required unless we are reverting to default
elif [ "$VALUE" == "" ] && [ $REVERT == false ]; then
   usage
fi;

#DEBUG
if [ $DEBUG == true ]; then
   echo "VAR=$VAR"
   echo "VALUE=$VALUE"
   echo "FORCE=$FORCE"
   echo "COMMENT=$COMMENT"
   echo "REVERT=$REVERT"
   
   if [ $FORCE == true ]; then
      echo "Force is true"
   fi
   
   if [ $COMMENT == true ]; then
      echo "Comment is true"
   fi

   if [ $REVERT == true ]; then
      echo "Revert is true"
   fi
   usage
fi;

TEST=$(grep -c "^# .*$VAR=" $CONFIG_FILE)
if [ $TEST -eq 0 ]; then
   EXISTS_COMMENTED=false
else
   EXISTS_COMMENTED=true
fi;
   
# If the setting does not exist commented out in the file already, exit with an error
if [ $EXISTS_COMMENTED == false ]; then
   echo "ERROR: $VAR does not exist commented out in the $CONFIG_FILE file"
   usage
else
   echo "Successfully Found $VAR commented out in the $CONFIG_FILE file"
fi;

TEST=$(grep -c -E "^\b$VAR=" $CONFIG_FILE)
if [ $TEST -eq 0 ]; then
   EXISTS_UNCOMMENTED=false
   if [ $REVERT == true ]; then
      echo "Did not find $VAR uncommented in the $CONFIG_FILE file. Cannot revert"
      usage
   fi
   echo "Did not find $VAR uncommented in the $CONFIG_FILE file."
else
   EXISTS_UNCOMMENTED=true
   echo "Also found $VAR uncommented in the $CONFIG_FILE file"
fi;

# If the setting exists uncommented in the file already, and we're not using and explicit flag to specify how to handle that, exit with an error
if [ $EXISTS_UNCOMMENTED == true ] && [ $FORCE == false ] && [ $COMMENT == false ] && [ $REVERT == false ]; then
   echo "ERROR: Re-run with an appropriate flag"
   echo
   grep "$VAR=" $CONFIG_FILE
   usage
fi;

# Before making any changes, backup the file
echo "Backing up $CONFIG_FILE to $CONFIG_FILE.bak"
rm -f $CONFIG_FILE.bak
cp $CONFIG_FILE $CONFIG_FILE.bak

# echo "Before..."
# grep -A2 -B2 "$VAR=" $CONFIG_FILE

if [ $COMMENT == true ]; then
# Just change the commented out version and leave it commented out
   sed -i "s/^# .*$VAR=.*/# $VAR=$VALUE/" $CONFIG_FILE
   echo "SUCCESS: Successfully changed commented out default setting for $VAR to $VALUE in $CONFIG_FILE"
elif [ $REVERT == true ]; then
# Just delete the uncommented line
   sed -i "/^$VAR=.*/d" $CONFIG_FILE
   echo "SUCCESS: Successfully reverted $VAR to commented out default in $CONFIG_FILE"
elif [ $EXISTS_UNCOMMENTED == true ]; then
# force change the existing uncommented value
   sed -i "s/^$VAR=.*/$VAR=$VALUE/" $CONFIG_FILE
   echo "SUCCESS: Successfully changed existing uncommented setting for $VAR to $VALUE in $CONFIG_FILE"
else
# The default behavior if no flags, copy the commented line and paste a new uncommented version below it with desired value
   sed -i "/^# .*$VAR=.*/p;s/# $VAR=.*/$VAR=$VALUE/" $CONFIG_FILE
   echo "SUCCESS: Successully changed $VAR from commented default to $VALUE in $CONFIG_FILE"
fi

# Show the changes we made and all non commented values
echo "Changes made to file..."
diff $CONFIG_FILE $CONFIG_FILE.bak
echo "All uncommented entries..."
grep -v "^#" $CONFIG_FILE | sort -u

exit
