#!/bin/sh
# Get images required by current serviced version
echo "Getting images and tags required by serviced"
serviced version | grep -i images | tr " " \\n | tail -n +2 | sed 's/[][]//g' > used_images.txt

# Get images required by current RM version
echo "Getting images and tags required by RM"
for s in $(serviced service list --show-fields ServiceID | grep -v ServiceID); do serviced service list $s | grep ImageID; done | cut -d'"' -f4 | awk '$1' | sort -u >> used_images.txt

# Get full list of docker images output
echo "Getting docker images output"
docker images | sort -u | grep -v REPOSITORY | grep -v "<none>" > docker_images.txt

# Search docker images output for images and tags potentially used, the field after the : in our used_images.txt file
echo "Getting list of images and tags potentially used"
# For each unique tag, grep docker images full output for that tag. Only images with such tags are potentially needed
for i in `cat used_images.txt | cut -d":" -f2 | sort -u`; do grep $i docker_images.txt; done | sort -u > potentials

# Now get a list of the actual images used rather than image tags from our potentials file, the field before the : 
# in our used_images.txt file
echo "Getting list of images used"
for i in `cat used_images.txt | cut -d":" -f1 | sort -u`; do grep $i potentials; done | sort -u > keep

# So in "keep" at this point, we have a very short list of the images and tag we need to keep
# Remove those from our original list of docker images and generate docker rmi commands for the rest
echo "Generating list of docker images/tags to remove"
comm docker_images.txt keep -23 | awk {'print "docker rmi " $1 ":" $2'} | sed 's/:<none>//' > remove_docker_images

# Remove unused images and tags
echo "Removing unused docker images/tags"
chmod +x remove_docker_images
./remove_docker_images

# Then remove any remaining docker images with no tags at all
echo "Removing all remaining docker images with no tags at all"
docker rmi $(docker images | grep "<none>" | awk '{print $3}') 2> /dev/null

# Cleanup
# rm used_images.txt
# rm docker_images.txt
# rm potentials
# rm keep
# rm remove_docker_images
