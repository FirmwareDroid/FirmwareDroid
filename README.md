[![Build Tests](https://github.com/FirmwareDroid/FirmwareDroid/actions/workflows/build_tests.yml/badge.svg)](https://github.com/FirmwareDroid/FirmwareDroid/actions/workflows/build_tests.yml)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
[![Open Source Love](https://badges.frapsoft.com/os/v2/open-source.svg?v=102)](https://github.com/ellerbrock/open-source-badge/)
[![Open Source Love](https://badges.frapsoft.com/os/gpl/gpl.svg?v=102)](https://github.com/ellerbrock/open-source-badge/)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)

# FirmwareDroid (FMD)
FirmwareDroid is a tool made for analysing Android firmware images. It is mainly made to automate the process 
of extracting and scanning pre-installed Android apps for security research purposes. FMD is made to run in 
docker and includes several third party analysis tools for security analysis and extraction. For instance:

* [AndroGuard](https://github.com/androguard/androguard)
* [Androwarn](https://github.com/maaaaz/androwarn/)
* [VirusTotal](https://www.virustotal.com)
* [Quark-Engine](https://github.com/quark-engine/quark-engine)
* [Qark](https://github.com/linkedin/qark/)
* [SUPER Android Analyzer](https://github.com/SUPERAndroidAnalyzer/super/)
* [APKiD](https://github.com/rednaga/APKiD/)
* [Exodus-Core](https://github.com/Exodus-Privacy/exodus-core/)
* [APKLeaks](https://github.com/dwisiswant0/apkleaks/)
* Fuzzy-Hashing (currently unavailable -> refactoring in progress)
  * [SSDeep](https://ssdeep-project.github.io/ssdeep/index.html)
  * [TLSH](https://tlsh.org/)
* [Unblob](https://github.com/onekey-sec/unblob)

In this repository you will find the code for the backend and documentation of the application. 
The application has a minimal and very limited React frontend (see https://github.com/FirmwareDroid/FMD-WebClient) 
but is mainly an API and database that can be use for research studies. 

### Prerequisites
* OS: 
  * Mac OSX
  * Ubuntu
  * Debian
* docker
* docker-compose
* python3
* pip3


### Usage

#### Getting started
1. Clone the repository and change to the FirmwareDroid directory
```
git clone --recurse-submodules https://github.com/FirmwareDroid/FirmwareDroid.git

cd FirmwareDroid
  ```
2. Install python packages for the setup:
```
pip3 install jinja2
```
3. Run the setup script:
```
python3 ./setup.py
```
4. Build the docker base images (takes some time).
```
chmod +x ./docker/build_docker_images.sh
./docker/build_docker_images.sh
```
5. Set correct access rights for the blob storage and start the containers
```
chown -R $(id -u):$(id -g) ./blob_storage
docker-compose up
```
The first start takes some time because the database will change the mode to a replica-set. 
Wait until the logscreen stops moving (takes usually 2 to 5 minutes).

6. Open the browser. By default, a self-signed certificates is used, and you will encounter a TLS warning.
```
https://fmd.localhost
```

7. Log-into the application. Password and username can be found in the `.env` file. 
```
cat .env
...
DJANGO_SUPERUSER_USERNAME=XXXXX
DJANGO_SUPERUSER_PASSWORD=XXXXX
...
```

8. After log-in, you can explore the following routes:
```
API: https://fmd.localhost/graphql
User-Management: https://fmd.localhost/admin
RQ-Job Management: https://fmd.localhost/django-rq
```

Note: To control FMD, the graphql API is used with an the interactive query builder, called GraphiQL. All
the examples in this doc use the graphql API available under https://fmd.localhost/graphql, which allows to
explore the API documentation and to build graphQL queries and mutations.

##### Importing firmware

After setting up the application, you might want to start exploring some Android firmware. By default, 
FMD creates a folder `blob_storage`, where all the data (databases and blobs) will be stored. To import Android firmware 
you need to copy the Android firmware archives (.zip, .tar) into the import folder: 
`blob_storage/00_file_storage/<random_id>/firmware_import`

1. Copy your firmware into the import folder:
```
`blob_storage/00_file_storage/<random_id>/firmware_import`
```
2. Navigate to the graphql API (https://fmd.localhost/graphql) and start the mutation job: `createFirmwareExtractorJob`
```
# First, log-in in case you haven't already
query MyQuery {
  tokenAuth(password: "XXXXX", username: "XXXX") {
    token
    payload
  }
}

# Second, start the import.
mutation StartImport {
  createFirmwareExtractorJob(createFuzzyHashes: false, 
  queueName: "high-python") {
    jobId
  }
}
```
Importing takes several minutes. Might be a good moment to get a coffee.

3. You can monitor the status of the job on https://fmd.localhost/django-rq or alternative you can connect directly to
the database to see if it was successfully imported. To connect to the database you need a MongoDb-client
(e.g., Studio 3T). You will find the connection credentials for mongodb in the `.env` file:
```
cat .env
...
MONGODB_USERNAME=XXXX
MONGODB_PASSWORD=XXXX
...
```
Connect to 127.0.0.1:27017 using SCRAM-SHA-256 authentication. You find all successfully imported firmware samples
in the collection `android_firmware`.

4. If the firmware was successfully imported you should have the collections `android_firmware` and `android_app` 
in the database, where you can find already some meta-data. Moreover, you can find the extracted 
apps within the blob storage:
```
APKs: `blob_storage/00_file_storage/<random-id>/android_app_store/<firmware-hash>/<partition-name>/`
Firmware: `blob_storage/00_file_storage/<random-id>/firmware_store/<android-version>/<firmware-hash>/`
Firmware (failed): `blob_storage/00_file_storage/<random-id>/firmware_import_failed/`
```
If for some reason the importer wasn't able to extract the firmware, the firmware will be moved to the 
`firmware_import_failed` directory in the blob storage and you need to check the docker logs why it failed.

You can also use the graphql API to fetch available firmware data with the following example queries:
```
# Gets a list of firmware object-ids
query GetAndroidFirmwareIds {
  android_firmware_id_list
}
```

Take the resulting firmware object-ids and use them for the following query to fetch some firmware meta-data.
(Replace XXXX with the firmware id you want to fetch)
```
query GetAndroidFirmwareIds {
  android_firmware_list(objectIdList: ["XXXXX"]) {
    absoluteStorePath
    fileSizeBytes
    filename
    hasFileIndex
    hasFuzzyHashIndex
    id
    indexedDate
    md5
    originalFilename
    osVendor
    relativeStorePath
    sha1
    sha256
    tag
    versionDetected
  }
}
```

You can fetch meta-data about the Android apps with the following two queries. (Replace XXXXX with the firmware id)
```
# Fetch Android app objects by firmware id.
query GetAndroidApps {
  android_app_list(
  objectIdList: ["XXXXX"], 
  documentType: "AndroidFirmware") {
    sha256
    sha1
    relativeStorePath
    relativeFirmwarePath
    pk
    packagename
    md5
    indexedDate
    id
    filename
    fileSizeBytes
    absoluteStorePath
  }
}
```

```
# Fetch just the Android app object-ids by the firmware-id
query GetAndroidAppIds {
  android_app_id_list_by_firmware(
    objectIdList: ["XXXXX"])
}
```


##### Scanning Android apps

Currently, FMD does not have a user interface for all features. To scan we use the graphql API. We are working 
on the FMD user-interface. However, since FMD is a research project our focus is currently mainly on enhancing the 
backend and not the frontend.

To scan Android apps, you will need to have the object-ids of the Android apps you want to scan. You can get the
object-ids directly from the database (collection: `android_app`) or via the graphql API.
1. To do it via graphql, navigate to https://fmd.localhost/graphql and run the following query to fetch the object-ids.
   (Replace XXXXXX with the firmware id.)
```
query GetAndroidAppIds {
  android_app_id_list_by_firmware(objectIdList: ["XXXXXX"])
}
```
As result, you will get a list of all the available Android app object-ids from the specified firmware. We can now
scan these Android apps with one of the static-analysers.

2. In this example, we use AndroGuard. However, you could use any of the following static-analysers as well. Please,
note that not every scanner was built for mass scanning and some of them might be slow in scanning speed.
```
  ANDROGUARD
  ANDROWARN
  APKID
  APKLEAKS
  EXODUS
  QUARKENGINE
  QARK
  SUPER 
```
We start a scan job with the `createApkScanJob` mutation on https://fmd.localhost/graphql. We use the mutation as
follows. (Replace XXXX with the Android app object-ids you want to scan. Set the moduleName option to one from the 
above list)
```
mutation MyMutation {
  createApkScanJob(
    moduleName: "ANDROGUARD"
    objectIdList: ["XXXXX", "XXXXX", "XXXXX", "XXXXX"]
    queueName: "default-python"
  ) {
    jobId
  }
}
```
3. After executing the mutation, the docker container named `apk_scanner-worker-1` should start scanning 
the Android apps. You can monitor the status of jobs on https://fmd.localhost/django-rq or 
take a look at the logs in docker with: `docker-compose logs -f apk_scanner-worker-1`

4. The results of the scan job can either be viewed over the graphql API or directly on the database
   (collection `apk_scanner_report` in the db). After scanning, a reference to the scan result 
is stored in the Android app document. For instance, 
when scanning with AndroGuard, apps will have a reference called `androguard_report_reference` holding a object-id
reference to the scanner report document (e.g., `androguard_report`).

If we want to fetch the results, we used the object-ids for the `androguard_report` from the android app object. 
(Replace XXXXX with the androguard_report object-ids)
```
query GetAndroGuardReports {
  androguard_report_list(
    objectIdList: ["XXXXX", "XXXXX", "XXXXX"]) {
    Cls
    androidVersionCode
    androidVersionName
    appName
    effectiveTargetVersion
    isAndroidtv
    id
    isLeanback
    isMultidex
    isSignedV1
    isSignedV2
    isSignedV3
    isValidApk
    isWearable
    mainActivity
    manifestXml
    maxSdkVersion
    minSdkVersion
    packagename
    permissionDetails
    permissionsDeclaredDetails
    reportDate
    scannerName
    scannerVersion
    targetSdkVersion
  }
}
```
As a result you will get the scanning result from AndroGuard.


### Citation & Dataset
More information about the framework and it's usage can be found as well in the [here](). 
If you use FirmwareDroid for you own research please cite our work.
``` 
@INPROCEEDINGS{FirmwareDroid,
  author={Sutter, Thomas and Tellenbach, Bernhard},
  booktitle={2023 IEEE/ACM 10th International Conference on Mobile Software Engineering and Systems (MOBILESoft)}, 
  title={FirmwareDroid: Towards Automated Static Analysis of Pre-Installed Android Apps}, 
  year={2023},
  month={May},
  pages={12-22},
  doi={10.1109/MOBILSoft59058.2023.00009}
}
```

### Contributing

We are happy to accept contributions to the software and documentation. Feel free to open a pull request with your
enhancements.

### Security

FMD has only a minimal set of security features and is not a production ready software. Use at you own risk.


### Changelog

#### 2024 - January

* **Breaking changes**: Beginning in 2024, Django and GraphQL take over the roles of the Flask web server and REST API. 
The updated interface boasts improved performance and stability, albeit with the trade-off of incompatibility with 
previous versions of FMD. While MongoDB, with MongoEngine, remains the chosen database engine, some modifications 
have been made to the database models.


### Documentation (deprecated -> under revision)
See our [online documentation](https://firmwardroid.readthedocs.io/en/latest/) for further information:
* [Installation guide](https://firmwardroid.readthedocs.io/en/latest/01_installation.html)
* [API documentation](https://firmwardroid.readthedocs.io/en/latest/06_code-documentation.html)

#### Building the docs
All Sphinx docs can be found within this repository in the 
[docs](https://github.com/FirmwareDroid/FirmwareDroid/tree/main/docs) folder.
The docs can be build with Sphinx as follows:
```
pip install -r requirements.txt
pip install -r requirements_docs.txt
cd /docs
make html
```
The docs should then be available as html under the `/docs/build/` folder. If something is missing in the docs please
open an issue or better a pull request.


### License:
FirmwareDroid is a non-profit research project licenced under the GNU General Public License v3.0
(see our [licence](https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md)). 


