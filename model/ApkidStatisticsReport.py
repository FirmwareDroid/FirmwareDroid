from mongoengine import DictField, LazyReferenceField
from model import ImageFile
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
    compiler_plot_dict = DictField(LazyReferenceField(ImageFile, required=False), required=False)

    obfuscator_reference_dict = DictField(required=False)
    obfuscator_count_dict = DictField(required=False)
    obfuscator_plot_dict = DictField(LazyReferenceField(ImageFile, required=False), required=False)

    packer_reference_dict = DictField(required=False)
    packer_count_dict = DictField(required=False)
    packer_plot_dict = DictField(LazyReferenceField(ImageFile, required=False), required=False)

    anti_vm_reference_dict = DictField(required=False)
    anti_vm_count_dict = DictField(required=False)
    anti_vm_plot_dict = DictField(LazyReferenceField(ImageFile, required=False), required=False)

    anti_disassembly_reference_dict = DictField(required=False)
    anti_disassembly_count_dict = DictField(required=False)
    anti_disassembly_plot_dict = DictField(LazyReferenceField(ImageFile, required=False), required=False)

    manipulator_reference_dict = DictField(required=False)
    manipulator_count_dict = DictField(required=False)
    manipulator_plot_dict = DictField(LazyReferenceField(ImageFile, required=False), required=False)
