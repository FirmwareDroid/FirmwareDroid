# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging

from scripts.hashing.fuzzy_hash_common import hash_sub_files
from model import TlshHash


def start_tlsh_hashing(firmware_file):
    """
    Starts the hashing with tlsh.
    :param firmware_file: class:'FirmwareFile
    :return:
    """
    logging.info(f"Create tlsh hash for: {firmware_file.absolute_store_path}")
    try:
        tlsh_hash = create_tlsh_hash(firmware_file)
        hash_sub_files(firmware_file, tlsh_hash, tlsh_from_file, tlsh_from_buffer)
    except Exception as err:
        logging.warning(err)


def create_tlsh_hash(firmware_file):
    """
    Creates a class:'TlshHash' document in the database.
    :param firmware_file: class:'FirmwareFile
    :return: class:'TlshHash'
    """
    digest = tlsh_from_file(firmware_file.absolute_store_path)
    tlsh_hash = TlshHash(
        firmware_id_reference=firmware_file.firmware_id_reference,
        firmware_file_reference=firmware_file.id,
        filename=firmware_file.name,
        tlsh_digest=digest,
        sub_file_digest_dict={}
    ).save()
    firmware_file.tlsh_reference = tlsh_hash.id
    firmware_file.save()
    return tlsh_hash


def tlsh_from_buffer(str_buffer):
    """
    Creates digest from the given buffer.
    :param str_buffer: str - to be hashed
    :return: str - digest
    """
    import tlsh
    return tlsh.hash(bytes(str_buffer, "utf-8"))


def tlsh_from_file(filepath):
    """
    Creates a digest from the given file.
    :param filepath: str
    :return: str  hash (ascii)
    """
    import tlsh
    h3 = tlsh.Tlsh()
    with open(filepath, 'rb') as f:
        for buf in iter(lambda: f.read(512), b''):
            h3.update(buf)
        h3.final()
    return h3.hexdigest()


def tlsh_compare_hashs(hash1, hash2):
    """
    Compare two fuzzy digests.
    :param hash1: str - digest
    :param hash2: str - digest
    :return: tlsh score
    """
    import tlsh
    return tlsh.diff(hash1, hash2)
