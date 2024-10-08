# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
from promise.utils import deprecated
from model import SsDeepHash

@deprecated(reason="SSDeep is not used anymore because it hasn't been updated for a long time.")
def create_ssdeep_hash(firmware_file):
    """
    Creates a class:'SsDeepHash' object for the given firmware file.

    :param firmware_file: class:'FirmwareFile'
    :return: class:'SsDeepHash'

    """
    logging.info(f"Creates ssdeep digest for file: {firmware_file.id} {firmware_file.name} "
                 f"{firmware_file.absolute_store_path}")
    ssdeep_digest = ssdeep_from_file(firmware_file.absolute_store_path)
    ssdeep_hash = SsDeepHash(digest=ssdeep_digest,
                             filename=firmware_file.name,
                             firmware_id_reference=firmware_file.firmware_id_reference,
                             firmware_file_reference=firmware_file.id)
    ssdeep_hash.save()
    if firmware_file.ssdeep_reference:
        firmware_file.ssdeep_reference.delete()
    firmware_file.ssdeep_reference = ssdeep_hash.id
    firmware_file.save()
    return ssdeep_hash


def ssdeep_from_buffer(str_buffer):
    """
    Creates a ssDeep hash from the given buffer.

    :param str_buffer: str - to be hashed
    :return: str ssdeep hash (ascii)

    """
    import ssdeep
    return ssdeep.hash(str_buffer)


def ssdeep_from_file(filepath):
    """
    Creates a ssDeep digest from the given file.

    :param filepath: str
    :return: str ssDeep hash (ascii)

    """
    import ssdeep
    return ssdeep.hash_from_file(filepath)


def ssdeep_compare_hashs(hash1, hash2):
    """
    Compare two fuzzy digests.

    :param hash1: ssDeep digest
    :param hash2: ssDeep digest
    :return: int (0-100) matching score

    """
    import ssdeep
    return ssdeep.compare(hash1, hash2)
