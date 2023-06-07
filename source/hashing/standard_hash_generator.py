# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import hashlib


def create_checksums_from_file(source):
    """
    Creates md5, sha1, sha256 checksum from file

    :param source:
    :return: md5, sha1, sha256

    """
    md5 = md5_from_file(source)
    sha1 = sha1_from_file(source)
    sha256 = sha256_from_file(source)
    return md5, sha1, sha256


def sha256_from_file(filepath):
    """
    Creates a sha256 from the given file.

    :param filepath: str
    :return: str sha256

    """
    h = hashlib.sha256()
    b = bytearray(128*1024)
    mv = memoryview(b)
    with open(filepath, 'rb', buffering=0) as f:
        for n in iter(lambda: f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()


def md5_from_file(filepath):
    """
    Creates a md5 from the given file.

    :param filepath: str
    :return: str md5

    """
    blocksize = 65536
    hasher = hashlib.md5()
    with open(filepath, 'rb') as afile:
        buf = afile.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(blocksize)
    return hasher.hexdigest()


def sha1_from_file(filepath):
    """
    Creates a sha1 from the given file.

    :param filepath: str
    :return: str sha1

    """
    blocksize = 65536
    hasher = hashlib.sha1()
    with open(filepath, 'rb') as afile:
        buf = afile.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(blocksize)
    return hasher.hexdigest()


def sha256_from_string(text):
    """
    Create a sha256 hash from a string.
    :param text: str
    :return: sha256 hex digest
    """
    hash_object = hashlib.sha512(bytes(text, 'utf-8'))
    return hash_object.hexdigest()


def sha256_from_bytes(bytes):
    """
    Create a sha256 hash from a byte buffer.
    :param bytes: bytes
    :return: sha256 hex digest
    """
    hash_object = hashlib.sha512(bytes)
    return hash_object.hexdigest()
