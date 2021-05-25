#!/bin/bash

echo "====================================================================================
# FirmwareDroid run script.
# Allows to start FirmwareDroid with different environment settings.
# Keep in mind to remove old docker containers when changing environments!
# Keep in mind to use the same environment as the one set in the .env file!
===================================================================================="

usage="
$(basename "$0") [-h] [-e <ENV>] [-r <RUN>] -- script to run FirmwareDroid in different environments.

where:
    -h  show this help text
    -e  set the environment (default: 0) (options: 0 = development, 1 = testing, 2 = production)
    -r  set the running mode (default: 0) (options: 0 = run, 1 = build intermediate images and run, 2 = build complete images and run)
    -d  run docker-compose detached
"

environment=0
running_mode=0
detached_mode=0
while getopts 'he:r:d' option; do
  case "$option" in
    h)  echo "$usage"
        exit 0
        ;;
    e)  if [ "$OPTARG" -eq "$OPTARG" ] 2>/dev/null; then
          environment=$OPTARG
        else
          printf "argument is not a number for -%s\n" "$OPTARG" >&2
          exit 1
        fi
       ;;
    r) if [ "$OPTARG" -eq "$OPTARG" ] 2>/dev/null; then
        running_mode=$OPTARG
       else
          printf "argument is not a number for -%s\n" "$OPTARG" >&2
          exit 1
       fi
       ;;
    d) detached_mode=1
       ;;
    :) printf "missing argument for -%s\n" "$OPTARG" >&2
       echo "$usage" >&2
       exit 1
       ;;
   \?) printf "illegal option: -%s\n" "$OPTARG" >&2
       echo "$usage" >&2
       exit 1
       ;;
  esac
done
shift $((OPTIND - 1))

echo "Environment set: $environment"
echo "Running mode set: $running_mode"

# Set docker-compose file and environment
if [ $environment == 1 ]; then
  compose_file="docker-compose.tst.yml"
  echo "Docker-compose environment: testing"
elif [ $environment == 2 ]; then
  compose_file="docker-compose.pro.yml"
  echo "Docker-compose environment: production"
else
  compose_file="docker-compose.dev.yml"
  echo "Docker-compose environment: development"
fi

# Run build
if [ $running_mode == 2 ]; then
  echo "Building all docker images"
  bash "./make/build_images_all.sh"
elif [ $running_mode == 1 ]; then
  echo "Building intermediate docker images"
  bash "./make/build_images_intermediate.sh"
fi
retVal=$?
if [ $retVal -ne 0 ]; then
    echo "Error - Could not build docker images!"
    exit $retVal
fi

compose_path=$PWD"/"$compose_file
# Run containers
if [ $detached_mode == 0 ]; then
  echo "Run docker compose"
  docker-compose -f $PWD"/docker-compose.yml" -f $compose_path up
else
  echo "Run docker compose detached"
  docker-compose -f $PWD"/docker-compose.yml" -f $compose_path up -d
fi
