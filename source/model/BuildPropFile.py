# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from mongoengine import FileField, DictField, CASCADE, LazyReferenceField, Document, signals
from model import AndroidFirmware, FirmwareFile


class BuildPropFile(Document):
    firmware_id_reference = LazyReferenceField(AndroidFirmware, reverse_delete_rule=CASCADE, required=False)
    firmware_file_id_reference = LazyReferenceField(FirmwareFile, reverse_delete_rule=CASCADE, required=True)
    build_prop_file = FileField(required=True, collection_name="fs.build_prop")
    properties = DictField(required=True)

    @classmethod
    def pre_file_delete(cls, sender, document, **kwargs):
        document.build_prop_file.delete()
        document.save()


signals.pre_delete.connect(BuildPropFile.pre_file_delete, sender=BuildPropFile)
