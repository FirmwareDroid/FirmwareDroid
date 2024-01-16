# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from abc import abstractmethod


class ScanJob:

    @abstractmethod
    def __init__(self, object_id_list):
        pass

    @abstractmethod
    def start_scan(self):
        pass




