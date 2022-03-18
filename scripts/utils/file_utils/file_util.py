# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import json
import ntpath
import os
import re
import shutil
import logging
import flask
from model import JsonFile
import tempfile
import time
from scripts.utils.encoder.JsonDefaultEncoder import DefaultJsonEncoder


def get_filenames(path):
    """
    Get list of all filenames from the given path
    """
    y = []
    try:
        x = [i[2] for i in os.walk(path)]
        for t in x:
            for f in t:
                y.append(f)
    except OSError:
        logging.exception("Could not search for files in given path: " + path)
    return y


def delete_files_in_folder(folder):
    """
    Deletes all files in the given folder
    """
    try:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
    except Exception as e:
        print(f'Failed to delete %s. Reason: {e}')


def delete_folder(dir_path):
    """
    Removes folder with content.

    :param dir_path: str - path of the folder to delete.

    """
    try:
        shutil.rmtree(dir_path)
    except OSError as e:
        print("Error: %s : %s" % (dir_path, e.strerror))


def delete_temporary_files(file_list):
    """
    Deletes all files from the given list.

    :param file_list: list(str)

    """
    for file in file_list:
        delete_file(file.name)


def delete_files_by_path(file_list):
    """
    Deletes all files from the given list.

    :param file_list: list(str)

    """
    for file in file_list:
        delete_file(file)


def delete_file(path):
    """
    Deletes a file from the filesystem

    :param path: str - to be removed

    """
    os.unlink(path)
    if os.path.exists(path):
        raise OSError(f"Could not delete file: {path}")


def create_temporary_file_from_list(string_list):
    """
    Creates a temporary files and writes all the given strings to the file.

    :param string_list: list(str)
    :return: class:'tempfile.NamedTemporaryFile'

    """
    app = flask.current_app
    file = tempfile.NamedTemporaryFile(delete=False, dir=app.config["FIRMWARE_FOLDER_CACHE"])
    with open(file.name, 'ab+') as file:
        for string_element in string_list:
            file.write(bytes(str(string_element), encoding='utf-8'))
            file.write(b'\n')
    delete_file(file.name)
    return file


def create_reference_file(string_list):
    json_tmp_file = object_to_temporary_json_file(string_list)
    return JsonFile(file=json_tmp_file.read()).save()


def create_reference_file_from_dict(string_dict):
    """
    Creates a class:'JsonFile' in which all reference from the given dict are written to.

    :param string_dict: dict(str, list(str (object-ids of class:'AndroidApp'))
    :return: dict(str, object-id of the class:'JsonFile' object)

    """
    reference_file_dict = {}
    for key, value in string_dict.items():
        json_tmp_file = object_to_temporary_json_file(string_dict[key])
        statistics_file = JsonFile(file=json_tmp_file.read()).save()
        reference_file_dict[key] = statistics_file.id
    return reference_file_dict


def binary_to_temp_file(binary):
    """
    Converts one binary to a tempfile.

    :param binary: The binary data to convert.
    :return: A temp_file.

    """
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(binary)
    return temp_file


def convert_binaries_to_file(binaries):
    """
    Converts a list of binaries to files.

    :param binaries: List of binaries.
    :return: array of temporary files.

    """
    file_list = []
    for binary in binaries:
        temp_file = binary_to_temp_file(binary)
        file_list.append(temp_file)
    return file_list


def create_directories(path):
    """
    Creates directory with subdirectories.

    :param path: str - path to create.

    """
    try:
        os.makedirs(path)
    except OSError:
        logging.error("Creation of the directory %s failed" % path)
    else:
        logging.info("Successfully created the directory %s" % path)


def copy_file(source, target):
    """
    Creates a copy of the given source to the target destination.

    :param source: str - path of the source file.
    :param target: str - path of the destination folder.
    :return: str - path of the copied file.

    """
    shutil.copy(source, target)
    file_name = ntpath.basename(source)
    return os.path.join(target, file_name)


def check_file_format(regex_patterns, filename):
    """
    Checks if the given pattern match the filename.

    :param regex_patterns: list(str) - regex pattern list.
    :param filename: str - filename
    :return: true - if one of the regex pattern matches the filename.

    """
    is_match = False
    for pattern in regex_patterns:
        if re.match(pattern, filename):
            is_match = True
            break
    return is_match


def str_to_file(str_to_write):
    """
    Write a dictionary to a temporary file as string.

    :param str_to_write: str or dict or list - an object to write as string to a file.
    :return: tempfile

    """
    tmp_file = tempfile.NamedTemporaryFile()
    f = open(tmp_file.name, "w")
    f.write(str(str_to_write))
    f.close()
    return tmp_file


def object_to_temporary_json_file(obj_to_write):
    """
    Write a string to a temporary file as json.

    :param obj_to_write: str - an object to write as json to a file.
    :return: Python.tempfile

    """
    tmp_file = tempfile.NamedTemporaryFile()
    input_file = open(tmp_file.name, "w")
    json.dump(obj_to_write,
              input_file,
              sort_keys=False,
              indent=4,
              separators=(',', ': '),
              cls=DefaultJsonEncoder)
    input_file.close()
    return tmp_file


def store_json_file(file):
    """
    Stores a json file in the database.

    :param file: file - must be json parsable.
    :return: class:'JsonFile'

    """
    json_file = JsonFile(file=file.read()).save()
    return json_file


def stream_to_json_file(file):
    """
    Stores a json file in the database.

    :param file: file - must be json parsable.
    :return: class:'JsonFile'

    """
    json_file = JsonFile()
    json_file.file.new_file()
    with open(file, 'rb') as infile:
        for line in infile:
            json_file.file.write(line)
    json_file.file.close()
    logging.info("Created Json file.")
    json_file.save()
    return json_file


def create_temp_directories():
    """
    Creates temporary directories.

    :return: tempdir, tempdir

    """
    app = flask.current_app
    cache_temp_file_dir = tempfile.TemporaryDirectory(dir=app.config["FIRMWARE_FOLDER_CACHE"], suffix="_extract")
    cache_temp_mount_dir = tempfile.TemporaryDirectory(dir=app.config["FIRMWARE_FOLDER_CACHE"], suffix="_mount")
    time.sleep(5)
    return cache_temp_file_dir, cache_temp_mount_dir


def cleanup_directories(firmware_file_path, firmware_app_store):
    """
    Moves failed files to the import failed folder. Removes intermediate files.

    :param firmware_file_path: str - path to the firmware file.
    :param firmware_app_store: str - path to application directory for apps.

    """
    app = flask.current_app
    shutil.move(firmware_file_path, app.config["FIRMWARE_FOLDER_IMPORT_FAILED"])
    try:
        shutil.rmtree(firmware_app_store)
    except FileNotFoundError:
        pass
