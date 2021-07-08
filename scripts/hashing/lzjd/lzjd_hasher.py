# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
from scripts.hashing.fuzzy_hash_common import hash_sub_files
from model import LzjdHash


def start_lzjd_hashing(firmware_file):
    """
    Create a sdhash for the given file.
    :param firmware_file: class:'FirmwareFile
    """
    logging.info(f"Create Lzjd hash for: {firmware_file.absolute_store_path}")
    try:
        lzjd_hash = create_lzdj_hash(firmware_file)
        hash_sub_files(firmware_file, lzjd_hash, lzjd_from_file, lzjd_from_buffer)
    except Exception as err:
        logging.warning(err)


def create_lzdj_hash(firmware_file):
    """
    Create a fuzzy hash based on the Lempel-Ziv Jaccard distance from a file. Stores the hash in the database.
    :param firmware_file: class:'FirmwareFile'
    :return: class:'LzdjHash'
    """
    lzjd_digest = lzjd_from_file(firmware_file.absolute_store_path)
    return LzjdHash(
        firmware_file_reference=firmware_file.id,
        filename=firmware_file.name,
        lzdj_digest=lzjd_digest,
        sub_file_digest_dict={}
    ).save()


def lzjd_from_buffer(str_buffer):
    """
    Creates digest from the given buffer.
    :param str_buffer: str - to be hashed
    :return: str - digest
    """
    from pyLZJD import digest
    return digest(str_buffer, processes=-1, mode="sh")


def lzjd_from_file(filepath):
    """
    Creates a digest from the given file.
    :param filepath: str
    :return: str hash
    """
    return lzjd_from_buffer(filepath)


def lzjd_compare_hashes(hash1, hash2):
    """
    Compare two fuzzy digests.
    :param hash1: str - digest
    :param hash2: str - digest
    """
    from pyLZJD import sim
    return 1.0-sim(hash1, hash2)
