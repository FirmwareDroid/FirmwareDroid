# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import tempfile
from model import AndroidApp

# TODO: Finish programming - Experimental feature.

def scan():
    from mobsfscan.mobsfscan import MobSFScan
    src = 'tests/assets/src/java/java_vuln.java'
    scanner = MobSFScan([src], json=True)
    scanner.scan()



