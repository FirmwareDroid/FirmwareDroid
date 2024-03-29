# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import DictField
from model.StatisticsReport import StatisticsReport

ATTRIBUTE_MAP = {"compiler": "compiler_count_dict",
                 "obfuscator": "obfuscator_count_dict",
                 "packer": "packer_count_dict",
                 "anti_vm": "anti_vm_count_dict",
                 "anti_disassembly": "anti_disassembly_count_dict",
                 "manipulator": "manipulator_count_dict"}


class ApkidStatisticsReport(StatisticsReport):
    compiler_reference_dict = DictField(required=False)
    compiler_count_dict = DictField(required=False)

    obfuscator_reference_dict = DictField(required=False)
    obfuscator_count_dict = DictField(required=False)

    packer_reference_dict = DictField(required=False)
    packer_count_dict = DictField(required=False)

    anti_vm_reference_dict = DictField(required=False)
    anti_vm_count_dict = DictField(required=False)

    anti_disassembly_reference_dict = DictField(required=False)
    anti_disassembly_count_dict = DictField(required=False)

    manipulator_reference_dict = DictField(required=False)
    manipulator_count_dict = DictField(required=False)
