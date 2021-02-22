import shlex
import subprocess
from scripts.utils.file_utils.file_util import copy_file


def attempt_repair(source, target):
    """
    Attempt to repair an image file with e2fsck.
    :param source: str - path of the image file.
    :return: path of the repaired file if successful or throws an exception if not.
    """
    backup_file_path = copy_file(source, target)
    exec_ext4_repair(backup_file_path)
    return backup_file_path


def attempt_repair_and_resize(source, target):
    """
    Attempt to repair an image file with e2fsck.
    :param source: str - path of the image file.
    :return: path of the repaired file if successful or throws an exception if not.
    """
    backup_file_path = attempt_repair(source, target)
    exec_ext4_resize(backup_file_path)
    return backup_file_path


def exec_ext4_repair(source):
    """
    Execute e2fsck with force auto-repair (-p) parameter.
    :param source: the file system to repair.
    """
    source = shlex.quote(source)
    subprocess.run(["e2fsck", "-p", source], timeout=600)


def exec_ext4_resize(source):
    """
    Execute resize2fs with force parameter.
    :param source: the file system to resize.
    """
    source_path = shlex.quote(str(source))
    subprocess.run(["resize2fs", "-f", source_path], timeout=600)
