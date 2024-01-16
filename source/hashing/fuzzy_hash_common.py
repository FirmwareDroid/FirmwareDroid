# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import re
import tempfile
from extractor.unzipper import extract_zip
from firmware_handler.const_regex_patterns import ELF_BINARY_FORMATS_PATTERN_LIST
from utils.file_utils.file_util import check_file_format
from database.mongodb_key_replacer import filter_mongodb_dict_chars


def hash_sub_files(firmware_file, fuzzy_hash_document, hash_from_file, hash_from_buffer):
    """
    Creates additional hashes for compressed data or specific code sections.

    :param firmware_file: class:'FirmwareFile'
    :param fuzzy_hash_document: document - Fuzzy hash document with sub files.
    :param hash_from_file: function - hashing function for files.
    :param hash_from_buffer: function - hashing function for buffers.

    """
    if firmware_file.name.endswith("apk"):
        hash_apk_file(firmware_file, fuzzy_hash_document, hash_from_file, hash_from_buffer)
    elif check_file_format(ELF_BINARY_FORMATS_PATTERN_LIST, firmware_file.name):
        identifier = firmware_file.name
        hash_elf_file(firmware_file.absolute_store_path, fuzzy_hash_document, identifier, hash_from_buffer)


def hash_apk_file(firmware_file, fuzzy_hash_document, hash_from_file, hash_from_buffer):
    """
    Creates a hash over the decompressed apk file.

    :param hash_from_file: function - hashing function for files.
    :param fuzzy_hash_document: document - Fuzzy hash document with sub files.
        :param hash_from_buffer: function - hashing function for buffers.
    :param firmware_file: class:'FirmwareFile'

    """
    temp_dir = tempfile.TemporaryDirectory(dir=flask.current_app.config["FIRMWARE_FOLDER_CACHE"])
    extract_zip(firmware_file.absolute_store_path, temp_dir.name)
    for root, dirs, files in os.walk(temp_dir.name):
        for file in files:
            file_path = os.path.join(root, file)
            identifier = file_path.replace(temp_dir.name, "")
            try:
                if file.endswith(".so"):
                    hash_elf_file(file_path, fuzzy_hash_document, identifier, hash_from_buffer)
                else:
                    fuzzy_hash_document.sub_file_digest_dict[str(identifier)] = hash_from_file(file_path)
            except Exception as err:
                logging.error(err)
    fuzzy_hash_document.sub_file_digest_dict = filter_mongodb_dict_chars(fuzzy_hash_document.sub_file_digest_dict)
    fuzzy_hash_document.save()


def hash_elf_file(file_path, fuzzy_hash_document, identifier, hash_from_buffer):
    """
    Creates additional fuzzy hashes for elf binaries. Hashes over every section in the elf file.

    :param hash_from_buffer: function - hashing function for buffers.
    :param identifier: str - unique identifier of the file.
    :param fuzzy_hash_document: document - Fuzzy hash document with sub files.
    :param file_path: str - filepath

    """
    import lief
    try:
        binary = lief.parse(file_path)
        if binary:
            fuzzy_hash_document.sub_file_digest_dict[identifier] = {}
            try:
                fuzzy_hash_document.sub_file_digest_dict[identifier]["header"] = hash_from_buffer(str(binary.header))
            except Exception as err:
                logging.warning(f"{file_path} - {err}")
            for section in binary.sections:
                try:
                    fuzzy_hash_document.sub_file_digest_dict[identifier][str(section.name)] \
                        = hash_from_buffer(str(section.content))
                except Exception as err:
                    logging.warning(f"{file_path} {section}- {err}")
            fuzzy_hash_document.sub_file_digest_dict = filter_mongodb_dict_chars(
                fuzzy_hash_document.sub_file_digest_dict)
            fuzzy_hash_document.save()
    except Exception as err:
        logging.error(f"Error parsing elf file {file_path} {err}")


def get_fuzzy_hash_documents_by_regex(regex_filter, document_class):
    """
    Gets a list of hash instances (document instances) of the given document class.

    :param regex_filter: str - regex to filter by filename attribute.
    :param document_class: mongoengine document - instance of the class to get the documents from.
    :return: list(document instances)

    """
    hash_document_list = []
    if not regex_filter:
        regex_filter = "[.]*"
    pattern = re.compile(regex_filter)
    for hash_instance in document_class.objects(filename=pattern):
        hash_document_list.append(hash_instance)
    return hash_document_list


def filter_fuzzy_hash_documents_by_firmware(fuzzy_hash_list, firmware_id_list):
    """
    Filters a list of fuzzy hash by firmware. If the file that the fuzzy hash belongs to is nit in the firmware it will
    be removed from the list.

    :param fuzzy_hash_list: list(document) - list of fuzzy hashes instances.
    :param firmware_id_list: list(str) - list of class:'FirmwareFile' object-id's
    :return: list(document) - list of filtered fuzzy hashes instances.

    """
    filtered_fuzzy_hash_list = []
    for fuzzy_hash in fuzzy_hash_list:
        if str(fuzzy_hash.firmware_id_reference.pk) in firmware_id_list:
            filtered_fuzzy_hash_list.append(fuzzy_hash)
    return filtered_fuzzy_hash_list
