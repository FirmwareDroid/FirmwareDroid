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
# Clone the repository
git clone https://github.com/FirmwareDroid/FirmwareDroid.git
cd FirmwareDroid

# Start FirmwareDroid
docker compose up -d
```

On first run, the `init` container automatically generates self-signed TLS certificates, MongoDB replica set credentials, Redis configuration, and Django administrator secrets into an isolated Docker volume (`fmd-config`).

### Retrieving Generated Credentials
View the generated administrator credentials in the `init` container logs:
```bash
docker compose logs init
```
Or copy the credentials summary to your current working directory:
```bash
docker compose cp init:/config/secrets/generated-secrets.txt .
```

### Configuration & Environment Variables (Optional)

By default, no `.env` file or pre-configuration is required. The `init` container dynamically provisions unique cryptographically random secrets on first startup into the `fmd-config` volume.

To customize configuration or provide your own secrets:
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Set custom variables in `.env` (such as `DJANGO_SECRET_KEY`, `DOMAIN_NAME`, database passwords, or storage paths). Values defined in `.env` take precedence over auto-generated defaults.


### Contributing

We are happy to accept contributions to the software and documentation. Feel free to open a pull request with your
enhancements or an issue with your suggestions. 

### Security

* **Secret Management:** FirmwareDroid enforces strict secret management. All credentials (Django `SECRET_KEY`, database passwords, cluster keys) are generated cryptographically at runtime and stored in an internal Docker volume (`fmd-config`). There are no insecure hardcoded secret fallbacks in the codebase. If running the backend outside Docker, `DJANGO_SECRET_KEY` is mandatory and must be provided via the environment.
* **Cookie & Transport Security:** Session and CSRF cookies enforce `Secure`, `HttpOnly`, and `SameSite=Strict` attributes to protect against session hijacking and cross-site scripting attacks.
* **CORS Restrictions:** Cross-Origin Resource Sharing (CORS) only allows the configured domain by default. Additional external domains can be explicitly whitelisted using `CORS_ADDITIONAL_HOST`.
* **Production Deployments:** FirmwareDroid is a research platform. For production deployments:
  * Replace the automatically generated self-signed TLS certificates in `/etc/nginx/live/` with valid CA-issued certificates (such as Let's Encrypt).
  * Avoid exposing internal database ports (`27017`, `6379`, `7474`) directly to the public internet.
  * Always use a dedicated `.env` file with strong, unique passwords.

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
