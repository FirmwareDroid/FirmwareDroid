#!/bin/bash
# Script that builds all the base dockerfiles for docker-compose

#####################################
# Parse Arguments                   #
#####################################
set -o errexit
set -o nounset
set -o pipefail

# Parse args
SERIAL=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    -s|--serial)
      SERIAL=true
      shift
      ;;
    *)
      echo "Usage: $0 [--serial|-s]"
      exit 1
      ;;
  esac
done

#####################################
# Frontend                           #
#####################################
docker build ./firmware-droid-client/ -f ./firmware-droid-client/Dockerfile -t firmwaredroid-frontend --platform="linux/amd64"
retVal=$?
if [ $retVal -ne 0 ]; then
    echo "Error building frontend"
    exit $retVal
fi

#####################################
# Backend                            #
#####################################
# Worker base
printf "Building FirmwareDroid BASE IMAGE\n"
docker build ./ -f ./Dockerfile_BASE -t firmwaredroid-base --platform="linux/amd64"
retVal=$?
if [ $retVal -ne 0 ]; then
    echo "Error building base image"
    exit $retVal
fi

# Build worker images
workers=(./docker/base/Dockerfile_*)
if [ "${#workers[@]}" -eq 0 ]; then
  echo "No worker Dockerfiles found in ./docker/base/"
else
  echo "Building worker images. This may take some time..."
  pids=()
  for i in "${workers[@]}"; do
    name=${i#*_}
    echo "Building image for: $name"
    if [ "$SERIAL" = true ]; then
      echo "Building worker: $name"
      docker build ./docker/base/ -f "./docker/base/Dockerfile_$name" -t "$name"-worker --platform="linux/amd64"
      retVal=$?
      if [ $retVal -ne 0 ]; then
        echo "Error building worker: $name"
        exit $retVal
      fi
    else
      docker build ./docker/base/ -f "./docker/base/Dockerfile_$name" -t "$name"-worker --platform="linux/amd64" &
      pids+=($!)
    fi
  done

  if [ "$SERIAL" = false ]; then
    # Wait for parallel builds to finish and fail on first non-zero exit
    for pid in "${pids[@]}"; do
      wait "$pid" || {
        echo "One of the worker builds failed (pid $pid)"
        exit 1
      }
    done
  fi
fi

docker compose build
retVal=$?
if [ $retVal -ne 0 ]; then
  echo "Error running docker compose build"
  exit $retVal
fi

echo "All builds completed successfully."