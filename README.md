[![Build Tests](https://github.com/FirmwareDroid/FirmwareDroid/actions/workflows/build_tests.yml/badge.svg)](https://github.com/FirmwareDroid/FirmwareDroid/actions/workflows/build_tests.yml)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
[![Open Source Love](https://badges.frapsoft.com/os/v2/open-source.svg?v=102)](https://github.com/ellerbrock/open-source-badge/)
[![Open Source Love](https://badges.frapsoft.com/os/gpl/gpl.svg?v=102)](https://github.com/ellerbrock/open-source-badge/)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)

# FirmwareDroid - Analysis tool for Android Firmware
FirmwareDroid is a tool made for analysing Android firmware images. It is made to automate the process 
of extracting and scanning pre-installed apps. It is a docker based webserver including several analysis tools and made
for scanning apps at scale.

## Requirements
Tested on Debian and OS X (Big Sur)

- docker
- docker-compose
- Storage: You need a lot of storage to run everything on one machine.
  - Docker: 50GB
  - File-store: at least 1.5x the storage of your firmware archives. (Depends on the number of pre-installed apps)
  - DB-Production:
    - DB: ~6000 firmware archives need around 200GB
  - DB-Dev:
    - DB: 50GB

## Installation (Linux)
- git clone https://github.zhaw.ch/suth/FirmwareDroid.git
- cd ./FirmwareDroid
- touch .env
  - Copy the example configuration to the .env file: https://github.zhaw.ch/suth/FirmwareDroid/blob/master/documentation/example_config/env.txt)
  - Configure the .env
- mkdir env
  - Copy all the files from the example env folder: https://github.zhaw.ch/suth/FirmwareDroid/tree/master/documentation/example_config/example_env)
  - Configure the files in the env folder:
    - mongo: Add your database users to the createusers.sh script.
    - redis: Add a passwort for your redis user in the redis.conf
    - certbot / nginx: Add your website certificate or just use the self signed example cert. You need to configure the
  app.conf paths for nginx.
- bash ./FirmwareDroid/build_all.sh
  - Note: This will take a long time since now all the docker images get created. Grab a coffee.

### Start FirmwareDroid:
- sh ./FirmwareDroid/build.sh

By default the start script creates a working directory named "00_file_storage". Following an overview of the folders:
- import: All Android firmware archives (.zip) in this folder will be imported to FirmwarDroid's database.
- import_failed: FirmwareDroid moves firmware archives in this folder that could not be imported.
- store: In this directory all firmware is stored for later access.
- app_extract: FirmwareDroid puts the extracted pre-installed apps into this folder.
- cache: Temporary directory for extracting and mounting files.

Note: First run can be rough. Be patient and let the docker containers run some time. In case of errors:
- Check your .env file
- Check your env configuration
- Run the build_all.sh and build.sh scripts again.
- Open https://localhost/docs in your browser.

### Getting started:
We recommend to use for all the examples the swagger page available at: http://localhost/docs. As an alternative
curl can be used and the all routes are under http://localhost/api/v1/... available.

Importing firmware:
After the installation you can start importing firmware samples by putting the archives (.zip) in the "import" folder.
- Put firmware into "import" folder
- Start the import with an HTTP get to: /v1/firmware/mass_import/
  - Alternative: curl -X GET "http://localhost/api/v1/firmware/mass_import/" -H "accept: application/json"
- You should see in the server console that the import has started. This can take some time.

Scanning:
You can either scan a list of android apps provided as JSON array or the complete dataset. Some routes 
use therefore a parameter "mode" to specific what to scan. Here an overview of different modes:
- mode 0: Scan only the provided android document id's (JSON)
- mode 1: Scan all firmware in the database.
- mode >1: Scan all app for a given firmware version. For example, mode = 8 --> All Android 8 firmware.

APKiD:
  - POST request to /v1/apkid/{mode}

AndroGuard:
  - POST request to /v1/androguard/{mode}

Androwarn:
  - Post request to /v1/androwarn/{mode}

Qark:
  - Post request to /v1/qark/{mode}

### Stop FirmwareDroid:
- cd ./FirmwareDroid
- docker-compose stop

### Uninstall FirmwareDroid:
- docker-compose stop
- rm -R ./FirmwareDroid
- Delete all docker containers, images, networks: docker system prune


## Architecture
- Frontend: NGINX with React (experimental)
- Backend: Flask with Gevent
- Database: mongodb

It is a docker-compose based web-application with several scanners. 
You can scale the number of docker containers manually via the docker-compose file.

## Contribution

- Pull-Requests: Are always welcome.
- Discussion / Ideas / Feedback: Open an issue with one of our templates. 
  Do not hesitate to get in touch with us and send us your feedback.

## About 
This project was part of my master thesis at the Zurich University of Applied Sciences. Please cite my work if you use 
FirmwareDroid for your research. The project is non-profit and you are allowed to use it in any form (see our copyright).




## Copyright
FirmwareDroid is licenced under the GNUv3 
(see [licence](https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md)). 


### Third Party Software Distributed with FirmwareDroid:
The FirmwareDroid software contains code written by third parties. Such software will
have its own individual licences. You as a user of this project must review, 
accept and comply with the license terms of each downloaded/installed 
package listed below or in our requirements files. By proceeding with the installation, 
you are accepting the license terms of each package, and acknowledging that your 
use of each package will be subject to its respective license terms.

List of third party software:

[AndroGuard](https://github.com/androguard/androguard/blob/master/LICENCE-2.0),
[Androwarn](https://github.com/maaaaz/androwarn/blob/master/COPYING),
[APKiD](https://github.com/rednaga/APKiD/blob/master/LICENSE.COMMERCIAL),
[Exodus-Core](https://github.com/Exodus-Privacy/exodus-core/blob/v1/LICENSE), 
[Qark](https://github.com/linkedin/qark/blob/master/LICENSE),
[Quark-Engine](https://github.com/quark-engine/quark-engine),
