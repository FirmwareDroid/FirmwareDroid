# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import flask
from dynamic_analysis.emulator_control.adb.adb_wrapper import push_file, file_exists, \
    send_shell_command_streamed, adb_root

# TODO REMOVE OF FINISH WORK HERE

def install_frida_server(adb_device, frida_port):
    app = flask.current_app
    adb_root(adb_device)
    libs_path = app.config["LIBS_FOLDER"]
    frida_filename = "frida-server"
    local_path = libs_path + frida_filename
    device_path = "/data/local/tmp/"
    binary_path = device_path + frida_filename
    logging.info(f"local_path: {local_path}")
    logging.info(f"device_path: {device_path}")
    logging.info(f"binary_path: {binary_path}")
    frida_binary_exists = file_exists(adb_device, binary_path)
    if not frida_binary_exists:
        push_file(adb_device, local_path, binary_path)
    logging.info(f"Start frida server on all interfaces:{binary_path}")
    command_list = [f"chmod 755 {binary_path}", f"{binary_path} --listen=0.0.0.0:{frida_port} -v"]
    try:
        for command in command_list:
            logging.info(f"Execute command: {command}")
            response = send_shell_command_streamed(adb_device, command)
            for element in response:
                logging.info(f"element: {element}")
    except Exception as err:
        logging.error(err)


def frida_smoke_test(device_ip, device_port):
    logging.info(f"Start frida smoke test")
    import frida
    try:
        frida_server = frida.get_device_manager().add_remote_device(f"{device_ip}:{device_port}")
        logging.info(f"Try device: {frida_server}")
        app_list = frida_server.enumerate_applications()
        for element in app_list:
            logging.info(element)
    except Exception as err:
        logging.error(err)
    logging.info(f"End frida smoke test")


def frida_attach_pid(packagename_list):
    import frida
    frida_server = frida.get_remote_device()
    pid_list = []
    session_dict = {}
    for packagename in packagename_list:
        pid = frida_server.spawn([packagename])
        pid_list.append(pid)
        session_dict[pid] = frida_server.attach(pid)


def load_frida_script(session_dict, frida_script):
    # frida_script = FridaScript.objects.get(script_name="universal_SSL_pinning_bypass.med")
    for session in session_dict.values():
        script = session.create_script(frida_script.code)
        script.load()










