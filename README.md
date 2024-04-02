[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
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

In this repository you will find the code for the backend of FMD. The application has a minimal React
frontend (see https://github.com/FirmwareDroid/FMD-WebClient), but is mainly an API and database 
that can be use for research studies.

Usage documentation can be found at: https://firmwaredroid.github.io/

### Contributing

We are happy to accept contributions to the software and documentation. Feel free to open a pull request with your
enhancements.

### Security

FMD has only a minimal set of security features and is not a production ready software. Use at your own risk.
  
### License:
FirmwareDroid is a non-profit research project licenced under the GNU General Public License v3.0
(see our [licence](https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md)).
