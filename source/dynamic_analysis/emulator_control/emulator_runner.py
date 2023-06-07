import logging
import os
from mongoengine import DoesNotExist
from dynamic_analysis.frida.frida_server_installer import install_frida_server, frida_smoke_test
from model import AndroidApp
from dynamic_analysis.emulator_control.adb.adb_wrapper import load_adb_rsa_signer, connect_adb_device_tcp, \
    is_device_available, is_app_installed, install_app, push_file
from context.context_creator import push_app_context


# TODO REMOVE OR FINISH WORK HERE - Experimental
@push_app_context
def start_dynamic_analysis(emulator_url, emulator_port, android_app_id_list):
    """
    Experimental Feature
    """
    adb_device = open_emulator_connection(emulator_url, emulator_port)
    #installed_apps_list = install_standard_android_apps(android_app_id_list, adb_device)
    #for packagename in installed_apps_list:
    #    result = run_monkey(adb_device, packagename)
    #    logging.info(f"Monkey result {packagename}: {result}")


def start_frida_server_installation(emulator_url, emulator_port, frida_port):
    adb_device = open_emulator_connection(emulator_url, emulator_port)
    install_frida_server(adb_device, frida_port)


def start_frida_smoke_test(device_ip, frida_port):
    frida_smoke_test(device_ip, frida_port)


def open_emulator_connection(emulator_url, emulator_port):
    """
    Opens an adb connection to the standard emulator_control.
    """
    rsa_signer = load_adb_rsa_signer()
    adb_device = connect_adb_device_tcp(emulator_url, emulator_port, rsa_signer)
    is_connected = is_device_available(adb_device)
    if not is_connected:
        ValueError(f"Could not connect ADB device {emulator_url}:{emulator_port}")
    logging.info(f"ADB device {emulator_url}:{emulator_port} is connected: {is_connected}")
    return adb_device


def install_standard_android_apps(android_app_id_list, adb_device):
    """
    Attempts to install android apps over the package manager.
    :param android_app_id_list: list(str) - list of object-id's for class:'AndroidApp'
    :param adb_device: class:'adb_shell.AdbDeviceTcp'
    :return: list(class:'AndroidApp') - list of Android App instances that were installed.
    """
    installed_apps_list = []
    for android_app_id in android_app_id_list:
        try:
            android_app = AndroidApp.objects.get(pk=android_app_id)
            if not android_app.androguard_report_reference:
                raise ValueError(f"Could not install app {android_app.filename} {android_app.id}: No AndroGuard "
                                 f"Report available!")
            androguard_report = android_app.androguard_report_reference.fetch()
            device_path = "/data/local/tmp/" + os.path.basename(android_app.absolute_store_path)
            push_file(adb_device, android_app.absolute_store_path, device_path)
            logging.info(f"install_path: {device_path}")
            result = install_app(adb_device, device_path)
            if not is_app_installed(adb_device, androguard_report.packagename):
                raise ValueError(f"Could not install app {android_app.filename} {android_app.id}: {result}")
            installed_apps_list.append(androguard_report.packagename)
        except (DoesNotExist, ValueError) as err:
            logging.error(err)
    return installed_apps_list








