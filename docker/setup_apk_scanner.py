import os
import shutil
import subprocess
from venv import create

INSTALLATION_PATH = "/opt/firmwaredroid/python/"
PYTHON_SCANNERS = [
    "androguard",
    "androwarn",
    "apkid",
    "apkleaks",
    "exodus",
    "qark",
    "quark_engine",
    "virustotal",
    "manifest_parser",
    "mobsfscan",
    "apkscan",
    "flowdroid",
    "trueseeing",
    "trufflehog",
]

CLIENT_REQ_FILE = "/var/www/requirements/requirements_scanner_client.txt"
FALLBACK_REQ_FILE = "/var/www/requirements.txt"
base_req_file = CLIENT_REQ_FILE if os.path.isfile(CLIENT_REQ_FILE) else FALLBACK_REQ_FILE

for scanner_name in PYTHON_SCANNERS:
    venv_dir = os.path.join(INSTALLATION_PATH, scanner_name)
    # Maintain strict isolated execution environment per tool to avoid dependency conflicts
    create(venv_dir, with_pip=True, system_site_packages=False)
    pip_bin = os.path.join(venv_dir, "bin", "pip")
    print(f"[{scanner_name}] Initializing isolated environment: {venv_dir}")

    scanner_req_file = f"/var/www/requirements/requirements_{scanner_name}.txt"
    install_args = [pip_bin, "install", "--no-cache-dir", "-r", base_req_file]
    if os.path.isfile(scanner_req_file) and os.path.getsize(scanner_req_file) > 0:
        install_args.extend(["-r", scanner_req_file])

    subprocess.run(install_args, check=True)

    # Clean up pip, setuptools and wheel from venv after installation to save ~10MB per venv
    try:
        subprocess.run([pip_bin, "uninstall", "-y", "pip", "setuptools", "wheel"],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

# Post-install cleanup: strip bytecode caches and test directories to minimize container size
for root, dirs, files in os.walk(INSTALLATION_PATH, topdown=True):
    # Prune bytecode caches and test suites in dependencies
    dirs_to_remove = [d for d in dirs if d in ("__pycache__", "tests", "test") and "site-packages" in root]
    for d in dirs_to_remove:
        shutil.rmtree(os.path.join(root, d), ignore_errors=True)
        dirs.remove(d)

    for f in files:
        if f.endswith((".pyc", ".pyo")):
            try:
                os.remove(os.path.join(root, f))
            except OSError:
                pass
