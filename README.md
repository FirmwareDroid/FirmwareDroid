[![Build Tests](https://github.com/FirmwareDroid/FirmwareDroid/actions/workflows/build_tests.yml/badge.svg)](https://github.com/FirmwareDroid/FirmwareDroid/actions/workflows/build_tests.yml)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
[![Open Source Love](https://badges.frapsoft.com/os/v2/open-source.svg?v=102)](https://github.com/ellerbrock/open-source-badge/)
[![Open Source Love](https://badges.frapsoft.com/os/gpl/gpl.svg?v=102)](https://github.com/ellerbrock/open-source-badge/)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)

# FirmwareDroid
FirmwareDroid is a tool made for analysing Android firmware images. It is made to automate the process 
of extracting and scanning pre-installed apps and other files from Android firmware images. It is a docker and 
docker-compose based framework including several third party analysis tools.

* [AndroGuard](https://github.com/androguard/androguard)
* [Androwarn](https://github.com/maaaaz/androwarn/)
* [VirusTotal](https://www.virustotal.com)
* [Quark-Engine](https://github.com/quark-engine/quark-engine)
* [Qark](https://github.com/linkedin/qark/)
* [SUPER Android Analyzer](https://github.com/SUPERAndroidAnalyzer/super/)
* [APKiD](https://github.com/rednaga/APKiD/)
* [Exodus-Core](https://github.com/Exodus-Privacy/exodus-core/)
* [APKLeaks](https://github.com/dwisiswant0/apkleaks/)
* Fuzzy-Hashing
  * [SSDeep](https://ssdeep-project.github.io/ssdeep/index.html)
  * [TLSH](https://tlsh.org/)

### Usage

A docker hub image for a simple installation is coming soon. Please refer to our [documentation](https://firmwardroid.readthedocs.io/en/latest/) 
to build the code yourself in the meantime.

### Building the code yourself
See our [online documentation](https://firmwardroid.readthedocs.io/en/latest/):
* [Installation guide](https://firmwardroid.readthedocs.io/en/latest/01_installation.html)
* [API](https://firmwardroid.readthedocs.io/en/latest/06_code-documentation.html)

### Building the docs
All Sphinx docs can be found within this repository in the 
[docs](https://github.com/FirmwareDroid/FirmwareDroid/tree/main/docs) folder.
The docs can be build with Sphinx:
```
pip install -r requirements.txt
pip install -r requirements_docs.txt
cd /docs
make html
```
The docs should then be available as html under the `/docs/build/` folder. If something is missing in the docs please
open an issue or better a pull request.


### Citation & Dataset
More information about the framework and it's usage can be found as well in the [here](). 
If you use FirmwareDroid for you own research please cite our work.
``` 
Bibtext citation comming soon
```

### License:
FirmwareDroid is a non-profit research project licenced under the GNU General Public License v3.0
(see our [licence](https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md)). 
