import logging
import os
import re

# TODO REMOVE OF FINISH WORK HERE
def load_adb_rsa_signer():
    """
    Loads the adb rsa keys and creates a signer object.

    :return: class:'adb_shell.auth.PythonRSASigner'

    """
    from adb_shell.auth.sign_pythonrsa import PythonRSASigner
    adbkey_path = os.path.expanduser("~/.android/adbkey")
    with open(adbkey_path) as f:
        priv = f.read()
    with open(adbkey_path + '.pub') as f:
        pub = f.read()
    return PythonRSASigner(pub, priv)


def connect_adb_device_tcp(url, port, rsa_signer):
    """
    Connect to the given url and port with adb.

    :param url: str - url of the device
    :param port: str - port of the device
    :param rsa_signer: class:'adb_shell.auth.PythonRSASigner' - signer object for adb keys.
    :return: class:'adb_shell.AdbDeviceTcp'

    """
    from adb_shell.adb_device import AdbDeviceTcp
    adb_device_tcp = AdbDeviceTcp(url, port, default_transport_timeout_s=30.)
    adb_device_tcp.connect(rsa_keys=[rsa_signer], auth_timeout_s=0.1)
    return adb_device_tcp


def is_device_available(adb_device):
    """
    Gets if the device is available:

    :param adb_device: class:'adb_shell.AdbDeviceTcp'
    :return: true if available.

    """
    return adb_device.available


def send_shell_command(adb_device, command):
    """
    Sends the given command via adb to the device.

    :param adb_device: class:'adb_shell.AdbDeviceTcp'
    :param command: str - adb command to execute.
    :return: The output of the ADB shell command as a string

    """
    return adb_device.shell(command,
                            transport_timeout_s=120.,
                            read_timeout_s=120.,
                            timeout_s=120.)


def send_shell_command_streamed(adb_device, command):
    return adb_device.streaming_shell(command,
                                      transport_timeout_s=None,
                                      read_timeout_s=30.)


def push_file(adb_device, local_path, device_path):
    """
    Push a file to the adb device.

    :param device_path: str - path on the device to copy to.
    :param local_path: str - source path of the file to copy.
    :param adb_device: class:'adb_shell.AdbDeviceTcp'
    :raises AdbConnectionError: in case the connection is not there.

    """
    adb_device._maxdata = 100*1024    # Bug fix for adb-shell connection to emulator.
    return adb_device.push(local_path, device_path,
                           progress_callback=push_progress_callback,
                           transport_timeout_s=30,
                           read_timeout_s=30)


def push_progress_callback(device_path, bytes_written, total_bytes):
    """
    Callback for pushing command. Logs the progress of the upload.
    """
    logging.info(f"ADB Push-Progress: {device_path} bytes_written:{bytes_written} total_bytes:{total_bytes}")


def start_app_by_activity(adb_device, packagename, activity):
    """
    Starts an app over the activity manager.

    :param adb_device: class:'adb_shell.AdbDeviceTcp'
    :param packagename: str - name of the package.
    :param activity: str - name of the activity to start.
    :return: The output of the ADB shell command as a string

    """
    command = f"am start -n {packagename}/{activity}"
    return send_shell_command(adb_device, command)


def install_app(adb_device, apk_path):
    """
    Send an install command for the given apk file.

    :param adb_device: class:'adb_shell.AdbDeviceTcp'
    :param apk_path: str - path to the apk.
    :return: The output of the ADB shell command as a string

    """
    command = f"pm install -g {apk_path}"
    return send_shell_command(adb_device, command)


def is_app_installed(adb_device, packagename):
    """
    Checks if the package is installed.

    :param adb_device: adb_device: class:'adb_shell.AdbDeviceTcp'
    :param packagename: str - package to check.
    :return: True if it is in the package manager list.

    """
    command = "pm list packages"
    package_list = send_shell_command(adb_device, command)
    match = re.search(packagename, package_list)
    return bool(match)


def adb_root(adb_device):
    """
    Change to root shell.

    :param adb_device: adb_device: class:'adb_shell.AdbDeviceTcp'

    """
    adb_device.root()


def list_dir(adb_device, device_path):
    """
    List directory of a device path.

    :return: list[DeviceFile] - Filename, mode, size, and mtime info for the files in the directory

    """
    return adb_device.list(device_path,
                           transport_timeout_s=30.,
                           read_timeout_s=30.)


def file_stat(adb_device, file_path):
    return adb_device.stat(file_path,
                           transport_timeout_s=30.,
                           read_timeout_s=30.)


def file_exists(adb_device, file_path):
    mode, size, mtime = file_stat(adb_device, file_path)
    logging.info(f"{file_path}:{mode}:{size}:{mtime}")
    return bool(mode)
