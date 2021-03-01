# Builds frontend and backend without requirements
docker build ./firmware-droid-client/ -f ./firmware-droid-client/Dockerfile -t firmwaredroid-frontend
retVal=$?
if [ $retVal -ne 0 ]; then
    echo "Error"
    exit $retVal
fi
docker-compose build
retVal=$?
if [ $retVal -ne 0 ]; then
    echo "Error"
    exit $retVal
fi