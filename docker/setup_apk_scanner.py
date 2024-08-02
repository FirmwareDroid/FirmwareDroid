import os
import subprocess
from venv import create

INSTALLATION_PATH = "/opt/firmwaredroid/python/"
PYTHON_SCANNERS = ["androguard",
                   "androwarn",
                   "apkid",
                   "apkleaks",
                   "exodus",
                   "qark",
                   "quark_engine",
                   "virustotal",
                   "manifest_parser",
                   "mobsfscan",
                   "apkscan"]

for scanner_name in PYTHON_SCANNERS:
    venv_dir = os.path.join(INSTALLATION_PATH, scanner_name)
    create(venv_dir, with_pip=True)
    pip3_env_path = os.path.join(venv_dir, "bin/python")
    print(f"{scanner_name}: {pip3_env_path}")
    pip_upgrade = subprocess.Popen([pip3_env_path, '-m', 'pip', 'install', '--upgrade', 'pip'])
    pip_upgrade.wait()
    main_install_process = subprocess.Popen([pip3_env_path, '-m', 'pip', 'install', '-r', '/var/www/requirements.txt'])
    main_install_process.wait()
    scanner_process = subprocess.Popen([pip3_env_path, '-m',
                      'pip', 'install', '-r', f'/var/www/requirements/requirements_{scanner_name}.txt'])
    scanner_process.wait()
