#!/bin/bash

########################################################################
# FirmwareDroid run script.
# Allows to start FirmwareDroid with different environment settings.
# Version: 1.0
# Created: 01.03.2021
# Author: Thomas Sutter
#########################################################################

usage="
$(basename "$0") [-h] [-e <ENV>] [-r <RUN>] -- script to run FirmwareDroid in different environments.

where:
    -h  show this help text
    -e  set the environment (default: 0) (options: 0 = development, 1 = testing, 2 = production)
    -r  set the running mode (default: 0) (options: 0 = run, 1 = build intermediate images and run, 2 = build complete images and run)
"

re='^[0-9]+$'
environment=0
running_mode=0
while getopts ':h:e:r:' option; do
  case "$option" in
    h)  echo "$usage"
        exit
        ;;
    e)  if [[ $OPTARG =~ $re ]]; then
          environment=$OPTARG
        else
          printf "argument is not a number for -%s\n" "$OPTARG" >&2
          exit 1
        fi
       ;;
    r) if [[ $OPTARG =~ $re ]]; then
        running_mode=$OPTARG
       else
          printf "argument is not a number for -%s\n" "$OPTARG" >&2
          exit 1
       fi
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
  export FLASK_ENV="testing"
  export FLASK_DEBUG="True"
  export APP_ENV="testing"
  export APP_DEBUG="True"
elif [ $environment == 2 ]; then
  compose_file="docker-compose.pro.yml"
  export FLASK_ENV="production"
  export FLASK_DEBUG="False"
  export APP_ENV="production"
  export APP_DEBUG="False"
else
  compose_file="docker-compose.dev.yml"
  export FLASK_ENV="development"
  export FLASK_DEBUG="True"
  export APP_ENV="development"
  export APP_DEBUG="True"
fi


# Run build
if [ $running_mode == 2 ]; then
  echo "Building all docker images"
  bash "./make/build_images_all.sh"
elif [ $running_mode == 1 ]; then
  echo "Building intermediate docker images"
  bash "./make/build_images_intermediate.sh"
fi
compose_path=$PWD"/"$compose_file
echo "########################################
Starting FirmwareDroid now
#######################################"
# Run app
docker-compose -f $PWD"/docker-compose.yml" -f $compose_path up