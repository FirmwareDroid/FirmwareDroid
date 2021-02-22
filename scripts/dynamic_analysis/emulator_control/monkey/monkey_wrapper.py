from scripts.dynamic_analysis.emulator_control.adb.adb_wrapper import is_device_available, send_shell_command


def run_monkey(adb_device, packagename):
    """
    Runs the monkey on the given package.
    :param adb_device: class:'adb_shell.AdbDeviceTcp'
    :param packagename: str - apk package name
    :return: str
    """
    if is_device_available(adb_device):
        package = f"monkey -p {packagename} -v 500"
        return send_shell_command(adb_device, package)
    else:
        raise ValueError("ADB device not available.")
