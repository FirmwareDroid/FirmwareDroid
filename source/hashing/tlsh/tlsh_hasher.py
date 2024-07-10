# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from model import TlshHash


def create_tlsh_hash(firmware_file):
    """
    Creates a class:'TlshHash' document without saving it in the database.

    :param firmware_file: class:'FirmwareFile - firmware file to be hashed.

    :return: class:'TlshHash' - tlsh hash document.

    """
    digest = get_tlsh_digest_from_file(firmware_file.absolute_store_path)
    tlsh_hash = TlshHash(
        firmware_id_reference=firmware_file.firmware_id_reference,
        firmware_file_reference=firmware_file.id,
        filename=firmware_file.name,
        digest=digest
    )
    tlsh_hash.save()
    if firmware_file.tlsh_reference:
        firmware_file.tlsh_reference.delete()
    firmware_file.tlsh_reference = tlsh_hash.id
    firmware_file.save()
    return tlsh_hash


def get_tlsh_digest_from_buffer(str_buffer):
    """
    Creates digest from the given buffer.

    :param str_buffer: str - to be hashed

    :return: str - digest

    """
    import tlsh
    return tlsh.hash(bytes(str_buffer, "utf-8"))


def get_tlsh_digest_from_file(filepath):
    """
    Creates a digest from the given file.

    :param filepath: str - path to the file

    :return: str - tlsh hash digest

    """
    import tlsh
    h3 = tlsh.Tlsh()
    with open(filepath, 'rb') as f:
        for buf in iter(lambda: f.read(512), b''):
            h3.update(buf)
        h3.final()
    return h3.hexdigest()


def tlsh_compare_digests(hash1, hash2):
    """
    Compare two tlsh digests and return the score.

    :param hash1: str - digest
    :param hash2: str - digest

    :return: int - tlsh score

    """
    import tlsh
    return tlsh.diff(hash1, hash2)
