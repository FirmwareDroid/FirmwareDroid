[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)

![FMD-HEADER.png](docs/FMD-HEADER.png)
# FirmwareDroid (FMD)
FirmwareDroid is a research project that aims to develop novel methods to analyse Android firmware. It is mainly made 
to automate the process of extracting and scanning pre-installed Android apps for security research purposes. In this 
repository you will find the code for the backend of FMD. The application has a minimal React
frontend (see https://github.com/FirmwareDroid/FMD-WebClient), but is mainly an API and database 
that can be used for research studies.

Usage **documentation** can be found at: https://firmwaredroid.github.io/

FMD is made to run in docker and includes several third party analysis tools for security analysis and extraction.
Some of the tools and features included are:

* Static-Analyzers for Android apps (APKs):
  * [AndroGuard](https://github.com/androguard/androguard)
  * [APKiD](https://github.com/rednaga/APKiD/)
  * [APKscan](https://github.com/LucasFaudman/apkscan)
  * [Exodus-Core](https://github.com/Exodus-Privacy/exodus-core/)
  * [FlowDroid](https://github.com/secure-software-engineering/FlowDroid)
  * [MobSFScan](https://github.com/MobSF/mobsfscan)
  * [Trueseeing](https://github.com/alterakey/trueseeing)
  * [TruffleHog](https://github.com/trufflesecurity/trufflehog)
  * [Quark-Engine](https://github.com/quark-engine/quark-engine)
  * [Qark](https://github.com/linkedin/qark/) (deprecated, no updates by the author)
  * [Androwarn](https://github.com/maaaaz/androwarn/) (deprecated, no updates by the author)
  * [SUPER Android Analyzer](https://github.com/SUPERAndroidAnalyzer/super/) (deprecated, discontinued by the author)
  * [APKLeaks](https://github.com/dwisiswant0/apkleaks/) (deprecated)
* APIs:
  * [VirusTotal](https://www.virustotal.com)
* Fuzzy-Hashing:
  * [SSDeep](https://ssdeep-project.github.io/ssdeep/index.html) (deprecated, no updates by the author)
  * [TLSH](https://tlsh.org/)
* Decompilers:
  * Android:
    * [Apktool](https://apktool.org/)
    * [Jadx](https://github.com/skylot/jadx)
    * [ASC](https://github.com/MG1937/ASC)
  * Java:
    * [CFR](https://github.com/leibnitz27/cfr)
    * [Procyon](https://github.com/mstrobel/procyon)
    * [Krakatau](https://github.com/Storyyeller/Krakatau)
* File and Firmware Extraction:
  * [Binwalk](https://github.com/ReFirmLabs/binwalk)
  * [Unblob](https://github.com/onekey-sec/unblob)
  * [Payload-Dumper](https://github.com/vm03/payload_dumper)
  * [Payload-Dumper-Go](https://github.com/ssut/payload-dumper-go)
  * [lpunpack](https://github.com/LonelyFool/lpunpack_and_lpmake/tree/android11)
  * [imgpatchtools](https://github.com/erfanoabdi/imgpatchtools)
* Miscellaneous:
  * AndroidManifest Parsing
* Dynamic Analysis:
  * Work in progress

FMD can be used as scanning engine for Android apps (.apk files), but it is mainly made to analyse pre-installed 
apps extracted from Android firmware. It allows you to extract various types of files from firmware images and creates
an inventory of the extracted files. The inventory can be used to scan the files with the included tools and APIs or to
analyse the collected data with custom tooling.

## Quick Start

FirmwareDroid supports zero-configuration startup out of the box with Docker Compose.

```bash
git clone https://github.com/FirmwareDroid/FirmwareDroid.git && cd FirmwareDroid && docker compose -f docker-compose-release.yml up -d && echo "Service started on https://fmd.localhost"
```
Starting a development environment with hot-reloading is also supported:
```bash
git clone https://github.com/FirmwareDroid/FirmwareDroid.git && cd FirmwareDroid && ./docker/build_images.sh && docker compose up -d && echo "Service started on https://fmd.localhost"
````

On first run, the `init` container automatically generates self-signed TLS certificates, MongoDB replica set credentials, Redis configuration, and Django administrator secrets into an isolated Docker volume (`fmd-config`).

### Retrieving Generated Credentials

For security, generated administrator credentials and database secrets are **never printed in cleartext to container logs**.
To retrieve your generated credentials, copy the credentials file from the isolated configuration volume to your host:

```bash
docker compose cp init:/config/secrets/generated-secrets.txt .
cat generated-secrets.txt
```

Alternatively, view them directly from a running container:
```bash
docker compose exec web cat /var/www/config/secrets/generated-secrets.txt
```

### Configuration & Environment Variables (Optional)

By default, no `.env` file or pre-configuration is required. The `init` container dynamically provisions unique cryptographically random secrets on first startup into the `fmd-config` volume.

To customize configuration or provide your own secrets:
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Set custom variables in `.env` (such as `DJANGO_SECRET_KEY`, `DOMAIN_NAME`, database passwords, or storage paths). Values defined in `.env` take precedence over auto-generated defaults.

#### File Storage Paths
FirmwareDroid organizes extracted firmwares, APKs, and analysis artifacts into isolated file stores (`00_file_storage` through `09_file_storage`).
- In Docker, these are mounted from the host `./blob_storage/0X_file_storage` into `/var/www/file_store/0X_file_storage`.
- You can override individual host mount locations using `LOCAL_STORAGE_PATH_00` through `LOCAL_STORAGE_PATH_09` in `.env`.
- The storage root within the backend container defaults to `FILE_STORE_ROOT=/var/www/file_store/`. When running outside Docker, it automatically defaults to `<project_root>/blob_storage/`.

### Contributing

We are happy to accept contributions to the software and documentation. Feel free to open a pull request with your
enhancements or an issue with your suggestions. 

### Security

FMD is a research project and should not be used in production environments. It is not hardened for production use and may contain security vulnerabilities. Please use it in a controlled environment only.

### Publications

[FirmwareDroid: Towards Automated Static Analysis of Pre-Installed Android Apps](https://ieeexplore.ieee.org/document/10172951)
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

### License:
FirmwareDroid is a non-profit research project licenced under the GNU General Public License v3.0
(see our [licence](https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md)).
