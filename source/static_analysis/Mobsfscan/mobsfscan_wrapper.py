import logging
import tempfile
from model import AndroidApp

# TODO: Finish programming - Experimental feature.

def scan():
    from mobsfscan.mobsfscan import MobSFScan
    src = 'tests/assets/src/java/java_vuln.java'
    scanner = MobSFScan([src], json=True)
    scanner.scan()



