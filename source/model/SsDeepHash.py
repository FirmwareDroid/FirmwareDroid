# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import base64
from struct import unpack
from mongoengine import StringField, ListField, IntField, LazyReferenceField, CASCADE, signals, Document


class SsDeepHash(Document):
    firmware_id_reference = LazyReferenceField('AndroidFirmware', reverse_delete_rule=CASCADE)
    firmware_file_reference = LazyReferenceField('FirmwareFile', reverse_delete_rule=CASCADE, required=True)
    filename = StringField(required=True)
    digest = StringField(required=True)
    block_size = StringField(required=False)
    block_data = StringField(required=False)
    double_block_data = StringField(required=False)
    chunk_7_set = ListField(field=IntField(), required=False)
    chunk_7_double_set = ListField(field=IntField(), required=False)

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        block_data, double_block_data, block_size, chunk_7_set, chunk_7_double_set \
            = preprocess_hash(document.ssdeep_digest)
        document.block_size = block_size
        document.block_data = block_data
        document.double_block_data = double_block_data
        document.chunk_7_set = chunk_7_set
        document.chunk_7_double_set = chunk_7_double_set


# Mongoengine Signals
signals.pre_save.connect(SsDeepHash.pre_save, sender=SsDeepHash)


def preprocess_hash(ssdeep_digest):
    """
    Adds meta information necessary to scale comparison of ssdeep hashs.
    Source and more info from: https://www.virusbulletin.com/virusbulletin/2015/11/optimizing-ssdeep-use-scale
    :param ssdeep_digest: str - ssDeep digest.
    :return: int, set(int), set(int)
    """
    block_size, ssdeep_parts = ssdeep_digest.split(":", 1)
    block_data, double_block_data = get_block_and_double_block_data(ssdeep_parts)
    return block_data, double_block_data, block_size, get_all_7_char_chunks(block_data), \
           get_all_7_char_chunks(double_block_data)


def get_all_7_char_chunks(digest_data):
    """
    Splits the chunks into 7 chars then base64 decodes them and save them as int.
    :param digest_data: str - ssDeep digest.
    :return: set(int)
    """
    return list(set((unpack("<Q", base64.b64decode(digest_data[i:i + 7] + "=")
                            + b"\x00\x00\x00")[0] for i in range(len(digest_data) - 6))))


def get_block_and_double_block_data(ssdeep_parts):
    """
    Gets the second and third part of the ssdeep digest.
    :param ssdeep_parts: str - second and third part of the ssDeep digest.
    :return: array[str, str] - block and double block data
    """
    for c in set(list(ssdeep_parts)):
        while c * 4 in ssdeep_parts:
            ssdeep_parts = ssdeep_parts.replace(c * 4, c * 3)
    return ssdeep_parts.split(":")
