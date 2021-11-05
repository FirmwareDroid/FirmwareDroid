Installation Guide
==================

Requirements
------------
Tested on Debian 10 and OSX (Big Sur).

**Hardware Requirements**
To work flawless, FirmwareDroid needs a lot of storage, memory, and cpu-power.

Development environment:
 * RAM: 16GB
 * CPU: 2.8 GHz Quad-Core Intel Core i7
 * Storage: 150GB

Production environment:
 * RAM: 400GB
 * CPU: 48 Cores
 * Storage-Database: 1TB

**Software Requirements**

- Supported platforms: Linux and OSX. (We will support Windows maybe in a later version.)
- git
- `docker <https://docs.docker.com/engine/install/>`_
- `docker-compose <https://docs.docker.com/compose/install/>`_


Installation (Linux)
--------------------
We recommend the installation on a Debian 10 or a similar Linux distribution.

1. git clone https://github.com/FirmwareDroid/FirmwareDroid
2. cd ./FirmwareDroid
3. touch .env
    - Copy the :ref:`example configuration <02_configuration>` to the .env file
    - Configure the .env
4. mkdir env
    - Copy all the files from the example env folder (:ref:`see configuration <02_configuration>`):
    - Configure the files in the env folder:
        - mongo: Add your database users to the createusers.sh script.
        - redis: Add a passwort for your redis user in the redis.conf
        - certbot / nginx: Add your website certificate or just use the self signed example cert. You need to configure the
  app.conf paths for nginx.
5. bash ./FirmwareDroid/build_all.sh
    - Note: This will take a long time since now all the docker images get created. Grab a coffee.

Getting started
---------------
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


Importing firmware and start scanning
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default FirmwareDroid will attempt to import all archives from the ``.../00_file_storage/firmware_import/`` folder.
To get started copy some firmware files into the folder and then open FirmwareDroid in your browser.

1. Login as admin on https://localhost/login
2. Navigate in the browser to https://localhost/admin and select the "Server Controls" tab.
3. Click on "Run Firmware Import"

The firmware import can take several minutes or even hours to finish, depending on the number of firmware archives you provided.
As soon as the import is finished you are able to start scanning.

1. Login as admin on https://localhost/login
2. Navigate in the browser to https://localhost/admin and select the "Server Controls" tab.
3. Select the scanner of your choice. For example AndroGuard: https://localhost/admin/scanner/0?
4. Select the apps you want to scan and click on "Scan selection"

You can monitor the all jobs via the RQ dashboard or the server console logs. Individual container
logs can be displayed via console:

1. Change to the root directory with ``cd FirmwareDroid/``
2. ``docker logs CONTAINER-NAME -f --tail=1000``

Exploring the API
~~~~~~~~~~~~~~~~~
**REST API**: By default a Swagger.io API documentation page is build and made available under https://localhost/apidocs. However,
before you can use the Swagger.io API you need to authenticate your user via https://localhost/login or set the cookie
manually. Please notice that the Swagger.io "Try it out" function will only work in development mode and is not available
for production builds.

**RQ Dashboard**: You can use the built-in RQ dashboard to monitor scanning jobs. The dashboard is available under the
route https://localhost/rq-dashboard/

**Elasticsearch**: To explore the Elasticsearch data a Kibana user interface is made available under
https://localhost:5602 and you can login with a basic authentication user and password. For more information about
ElasticSearch see our guide :ref:`here <11_elasticsearch>`.

Removing FirmwareDroid
~~~~~~~~~~~~~~~~~~~~~~~~
- docker-compose stop
- rm -R ./FirmwareDroid
- Deletes all docker containers, images, networks: docker system prune