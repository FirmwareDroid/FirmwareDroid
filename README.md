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

## Quick Start

FirmwareDroid now supports streamlined setup for faster deployment:

### Option 1: Instant Start (Recommended)
```bash
git clone --recurse-submodules https://github.com/FirmwareDroid/FirmwareDroid.git
cd FirmwareDroid
docker compose up
```

This will automatically:
- Create default configuration files
- Set up storage directories  
- Generate SSL certificates
- Start all services

Access FirmwareDroid at: `https://fmd.localhost`  
Default credentials: `fmd-admin` / `admin`

### Option 2: Quick Setup Script
```bash
git clone --recurse-submodules https://github.com/FirmwareDroid/FirmwareDroid.git
cd FirmwareDroid
./quick_setup.sh
docker compose up
```

### Option 3: Custom Configuration
```bash
git clone --recurse-submodules https://github.com/FirmwareDroid/FirmwareDroid.git
cd FirmwareDroid
python setup.py  # Interactive configuration
docker compose up
```

### Using Published Images
For production or if you prefer pre-built images:
```bash
git clone --recurse-submodules https://github.com/FirmwareDroid/FirmwareDroid.git
cd FirmwareDroid
./quick_setup.sh  # Create configuration
docker compose -f docker-compose-release.yml up
```

## Included Tools and Features

FMD is made to run in docker and includes several third party analysis tools for security analysis and extraction.
Some of the tools and features included are:

* Static-Analyzers for Android apps (APKs):
  * [AndroGuard](https://github.com/androguard/androguard)
  * [APKiD](https://github.com/rednaga/APKiD/)
  * [APKLeaks](https://github.com/dwisiswant0/apkleaks/)
  * [APKscan](https://github.com/LucasFaudman/apkscan)
  * [Exodus-Core](https://github.com/Exodus-Privacy/exodus-core/)
  * [FlowDroid](https://github.com/secure-software-engineering/FlowDroid)
  * [MobSFScan](https://github.com/MobSF/mobsfscan)
  * [Trueseeing](https://github.com/alterakey/trueseeing)
  * [Quark-Engine](https://github.com/quark-engine/quark-engine)
  * [Qark](https://github.com/linkedin/qark/) (deprecated, no updates by the author)
  * [Androwarn](https://github.com/maaaaz/androwarn/) (deprecated, no updates by the author)
  * [SUPER Android Analyzer](https://github.com/SUPERAndroidAnalyzer/super/) (deprecated, discontinued by the author)
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
  * [Unblob](https://github.com/onekey-sec/unblob)
  * [SRLabs extractor](https://github.com/srlabs/extractor)
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

### Contributing

We are happy to accept contributions to the software and documentation. Feel free to open a pull request with your
enhancements or an issue with your suggestions. 

### Security

FMD has only a minimal set of security features and is not a production ready software. Use at your own risk.

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
