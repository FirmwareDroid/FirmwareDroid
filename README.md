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
* [ElasticSearch](https://www.elastic.co/)

### Installation & Documentation

See our [online documentation]():
* [Installation guide]()
* [Developers guide]()
* [API]()

All Sphinx docs can be found within this repository in the [docs](https://github.com/FirmwareDroid/FirmwareDroid/tree/main/docs) folder.
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

More information about the framework and it's usage can be found as well in the [master thesis]() of Thomas Sutter 
or in our [research paper](). If you use FirmwareDroid for you own research please cite our work.

``` 
Bibtext citation comming soon
```
Our firmware dataset is free of charge available for accredited researchers. See [here]() for more information.

### Contributions

Please see our [developers guide]() for code contributions.

### Copyright and Third Party Software Distributed with FirmwareDroid:
FirmwareDroid is licenced under the GNU General Public License v3.0
(see [licence](https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md)). 

The FirmwareDroid software contains code written by third parties. Such software will
have its own individual licences. You as a user of this project must review, 
accept and comply with the license terms of each downloaded/installed 
package listed below or in our "requirements*.txt" files or /requirements/* folder. By proceeding with the installation, 
you are accepting the license terms of each package, and acknowledging that your 
use of each package will be subject to its respective license terms.

List of third party packages:

[AndroGuard](https://github.com/androguard/androguard/blob/master/LICENCE-2.0),
[Androwarn](https://github.com/maaaaz/androwarn/blob/master/COPYING),
[APKiD](https://github.com/rednaga/APKiD/blob/master/LICENSE.COMMERCIAL),
[APKLeaks](https://github.com/dwisiswant0/apkleaks/blob/master/LICENSE),
[Exodus-Core](https://github.com/Exodus-Privacy/exodus-core/blob/v1/LICENSE), 
[Qark](https://github.com/linkedin/qark/blob/master/LICENSE),
[Quark-Engine](https://github.com/quark-engine/quark-engine/blob/master/LICENSE),
[SUPER Android Analyzer](https://github.com/SUPERAndroidAnalyzer/super/blob/master/LICENSE),
[VirusTotal-Python](https://github.com/dbrennand/virustotal-python/blob/master/LICENSE),
[ext4extract](https://github.com/hexedit/ext4extract),
[imgpatchtools](https://github.com/erfanoabdi/imgpatchtools), ...
