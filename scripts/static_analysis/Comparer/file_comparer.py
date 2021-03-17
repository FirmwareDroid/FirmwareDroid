import shlex
import subprocess
import tempfile
import flask
from scripts.firmware.ext4_mount_util import exec_umount
from model import ComparerReportFirmware, FirmwareFile, AndroidFirmware
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.extractor.expand_archives import extract_and_mount_all


def start_firmware_comparer(firmware_id_a, firmware_id_b):
    """
    Creates an app context and starts the firmware differ.
    :param firmware_id_a: The main firmware to diff against.
    :param firmware_id_b: the second firmware to use for diff.
    """
    create_app_context()
    firmware_a = AndroidFirmware.objects.get(pk=firmware_id_a)
    firmware_b = AndroidFirmware.objects.get(pk=firmware_id_b)
    compare_firmware(firmware_a, firmware_b)


@DeprecationWarning
def compare_firmware(firmware_a, firmware_b):
    """
    Compares two firmware files.
    :param firmware_a: The main firmware to diff against.
    :param firmware_b: the second firmware to use for diff.
    """
    firmware_list = [firmware_a, firmware_b]
    root_mount_directory_list = []
    mount_lists = []
    for firmware in firmware_list:
        temp_dir = tempfile.TemporaryDirectory(dir=flask.current_app.config["FIRMWARE_FOLDER_CACHE"])
        root_temp_dir, mount_directory_list = extract_and_mount_all(firmware, cache_path=temp_dir)
        root_mount_directory_list.append(root_temp_dir)
        mount_lists.append(mount_directory_list)
    report_file = tempfile.NamedTemporaryFile()
    exec_linux_diff_directories(root_mount_directory_list[0].name, root_mount_directory_list[1].name, report_file.name)
    files_error_list, files_only_in_list, files_differ_list = parse_diff(report_file.name)
    create_comparer_report(report_file_path=report_file.name,
                           firmware_list=firmware_list,
                           files_error_list=files_error_list,
                           files_only_in_list=files_only_in_list,
                           files_differ_list=files_differ_list)
    for dir_list in mount_lists:
        for mount_directory in dir_list:
            exec_umount(mount_directory)


def create_comparer_report(report_file_path, firmware_list, files_error_list, files_only_in_list, files_differ_list):
    """
    Creates a instance of class:'ComparerReportFirmware' and save it to the database.
    :param report_file_path: str file path to the linux diff report.
    :param firmware_list: list of the two firmware files which were diffed.
    :param files_error_list: list of error files from diff parser.
    :param files_only_in_list: list of added or removed files from diff parser.
    :param files_differ_list: list of differ files from diff parser.
    :return: class:'ComparerReportFirmware'
    """
    firmware_id_reference_list = []
    for firmware in firmware_list:
        firmware_id_reference_list.append(firmware.id)
    with open(report_file_path, 'rb') as file:
        report = ComparerReportFirmware(report_file=file,
                                        firmware_id_reference_list=firmware_id_reference_list,
                                        files_error_list=files_error_list,
                                        files_only_in_list=files_only_in_list,
                                        files_differ_list=files_differ_list)
    report.save()
    return report


def parse_diff(diff_report_file_path):
    """
    Parse the output file from linux diff tool. Deletes the path of the temporary from the output.
    :param diff_report_file_path: str - path to the diff report file.
    and replaced with the firmware_id.
    :return: triple(list, list, list)
        - files_error_list: Contains all relative files-paths which were marked as error in diff.
        - files_only_in_list: Contains all string in format path:file which were marked "only in" in diff.
        - files_differ_list: Contains all relative files-paths which differ in diff.
    """
    files_error_list = []
    files_only_in_list = []
    files_differ_list = []
    with open(diff_report_file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            string_parts = line.split(" ")
            if line.startswith("diff"):
                files_error_list.append(string_parts[1])
            elif line.startswith("Files"):
                files_differ_list.append(string_parts[1])
            elif line.startswith("Only in "):
                differ_string = string_parts[2] + string_parts[3]
                files_only_in_list.append(differ_string)
    return files_error_list, files_only_in_list, files_differ_list


def create_file_name_list(firmware):
    """
    Creaates a list of file names from the given firmware.
    :param firmware: class:'AndroidFirmware'
    :return: list(str) - file names of class:'FirmwareFiles'
    """
    firmware_file_name_list = []
    for lazy_file_id in firmware.firmware_file_id_list:
        firmware_file = FirmwareFile.objects.get(firmware_id_reference=lazy_file_id.fetch().id)
        firmware_file_name_list.append(firmware_file.name)
    return firmware_file_name_list


def exec_linux_diff_directories(folder_a, folder_b, output_file_path):
    """
    Execute the linux diff commands on the given folders.
    :param output_file_path: str - path to the file were the diff result is stored.
    :param folder_a: str path of the folder to diff.
    :param folder_b: str path of the folder to diff.
    """
    folder_a = shlex.quote(folder_a)
    folder_b = shlex.quote(folder_b)
    output_file = open(output_file_path, "w")
    subprocess.run(["diff", "-rq", folder_a, folder_b], timeout=600, stdout=output_file, stderr=output_file)