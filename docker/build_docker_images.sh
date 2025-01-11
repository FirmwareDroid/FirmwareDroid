#!/bin/bash

# Script that builds all the base dockerfiles for docker-compose
#####################################
#Frontend                           #
#####################################
docker build ./firmware-droid-client/ -f ./firmware-droid-client/Dockerfile -t firmwaredroid-frontend --platform="linux/amd64"
retVal=$?
if [ $retVal -ne 0 ]; then
    echo "Error"
    exit $retVal
fi

#####################################
#Backend                            #
#####################################
# Worker base
printf "Building FirmwareDroid BASE IMAGE"
docker build ./ -f ./Dockerfile_BASE -t firmwaredroid-base --platform="linux/amd64"
retVal=$?
if [ $retVal -ne 0 ]; then
    echo "Error"
    exit $retVal
fi

# Build worker images
workers=(./docker/base/Dockerfile_*)
echo "Building worker images. This is gonna take some time..."
for i in "${workers[@]}"; do
  name=${i#*_}
  echo "Building image for: ""$name"
  docker build ./docker/base/ -f ./docker/base/Dockerfile_"$name" -t "$name"-worker --platform="linux/amd64" &
done
if [ $retVal -ne 0 ]; then
  echo "Error"
  exit $retVal
fi
docker compose build