import logging
import os
import subprocess


def check_jadx_env():
    """
    Check if the jadx path is set in the environment variables.

    :return: bool - True if the jadx path is set, False otherwise.

    """
    jadx_path = os.getenv("JADX")
    if jadx_path is None or os.path.exists(jadx_path) is False:
        logging.error("The jadx path is not set in the environment variables.")
        return False
    return True


def check_apk_path(apk_path):
    """
    Check if the apk path is valid.

    :param apk_path: str - path to the apk file.

    :return: bool - True if the apk path is valid, False otherwise.

    """
    if not os.path.exists(apk_path) and not os.path.isfile(apk_path) and not apk_path.endswith(".apk"):
        logging.error(f"APK file not found at: {apk_path}")
        return False
    return True


def check_destination_dir(destination_dir):
    """
    Check if the destination directory is valid.

    :param destination_dir: str - path to the destination directory.

    :return: bool - True if the destination directory is valid, False otherwise.

    """
    if not os.path.exists(destination_dir) and not os.path.isdir(destination_dir):
        logging.error(f"Destination directory not found at: {destination_dir}")
        return False
    return True


def decompile_with_jadx(apk_path, destination_dir):
    """
    Decompile an Android app with jadx.

    :param apk_path: str - path to the apk file.
    :param destination_dir: str - path to the destination directory.

    :return: bool - True if the decompilation was successful, False otherwise.

    """
    is_successful = False
    jadx_path = os.getenv("JADX")
    jadx_path = os.path.join(jadx_path, "jadx")
    jadx_path = os.path.abspath(jadx_path)
    if (check_jadx_env() is False
            or check_apk_path(apk_path) is False
            or check_destination_dir(destination_dir) is False):
        logging.error("Decompilation with jadx failed. Could not check the environment variables or the paths.")
        return is_successful

    cmd = [jadx_path, "-d", destination_dir, apk_path]
    logging.info(f"Decompiling {apk_path} with jadx.")
    try:
        subprocess.run(cmd, check=True)
        is_successful = True
    except subprocess.CalledProcessError as err:
        logging.error(f"Jadx could not decompile {apk_path}. Error: {err}")
    return is_successful
