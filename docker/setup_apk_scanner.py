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
                   "virustotal"]

for scanner_name in PYTHON_SCANNERS:
    venv_dir = os.path.join(INSTALLATION_PATH, scanner_name)
    create(venv_dir, with_pip=True)
    pip3_env_path = os.path.join(venv_dir, "bin/python")

    subprocess.Popen([pip3_env_path, '-m', 'pip', 'install', '-r', '/var/www/requirements.txt'])
    subprocess.Popen([pip3_env_path, '-m',
                      'pip', 'install', '-r', f'/var/www/requirements/requirements_{scanner_name}.txt'])
