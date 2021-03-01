#!/bin/bash

# Script that builds all the base dockerfiles for docker-compose

#####################################
#Frontend                           #
#####################################
# React base
docker build ./firmware-droid-client/ -f ./firmware-droid-client/Dockerfile_BASE -t firmwaredroid-frontend-base
retVal=$?
if [ $retVal -ne 0 ]; then
    echo "Error"
    exit $retVal
fi
#NGINX Base
docker build ./firmware-droid-client/ -f ./firmware-droid-client/Dockerfile -t firmwaredroid-frontend
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
docker build ./ -f ./Dockerfile_BASE -t firmwaredroid-base
retVal=$?
if [ $retVal -ne 0 ]; then
    echo "Error"
    exit $retVal
fi

# Java Base
echo "Building JAVA BASE IMAGE"
docker build ./ -f ./Dockerfile_BASE_JAVA -t firmwaredroid-base-java
retVal=$?
if [ $retVal -ne 0 ]; then
    echo "Error"
    exit $retVal
fi

# Build worker images
workers=("androguard" "androwarn" "apkid" "exodus" "firmware" "frida" "fuzzyhash" "qark" "quark_engine" "virustotal")
echo "Building worker base images"
for i in "${workers[@]}"
do
  echo "Building image for: "$i
  docker build ./docker/base/ -f ./docker/base/Dockerfile_$i -t $i-worker
  retVal=$?
  if [ $retVal -ne 0 ]; then
      echo "Error"
      exit $retVal
  fi
done
docker-compose build