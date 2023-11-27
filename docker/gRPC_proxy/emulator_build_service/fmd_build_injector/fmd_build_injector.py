"""
A command-line tool that downloads files related to the build process of an Android firmware image and stores them
on disk. Directly extract the downloaded zip content.
"""
import os
import argparse
import re
import zipfile
import requests
from werkzeug.utils import secure_filename
from getpass import getpass
from tqdm import tqdm


def download_zip(url, object_id, jwt, output):
    """
    Downloads the build files for the given Android app (object id) and shows a progress bar of the download.

    :param url: str - base url of the FirmwareDroid backend.
    :param object_id: str - document reference to the Android app to download.
    :param jwt: str - authentication token.
    :param output: str - destination folder where the downloaded content will be stored.

    :return: str - path to the downloaded file.

    """
    download_url = url + "download/android_app/build_files/?object_id=" + object_id
    headers = {'Authorization': 'Bearer {}'.format(jwt)}

    response = requests.get(download_url, stream=True, headers=headers)
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)

    d = response.headers['content-disposition']
    filename_unsafe = re.findall("filename=(.+)", d)[0]
    filename = secure_filename(filename_unsafe)
    path = os.path.join(output, filename)
    with open(path, mode="wb") as file:
        for chunk in response.iter_content(chunk_size=10 * 1024):
            progress_bar.update(len(chunk))
            file.write(chunk)
    progress_bar.close()
    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        print("ERROR, something went wrong")

    return path


def extract_zip(file_path, destination):
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(destination)


def get_app_list(url, jwt, firmware_id):
    headers = {'Authorization': 'Bearer {}'.format(jwt)}
    # TODO add correct URL to fetch app object ids
    fetch_url = url + "/graphql/" + firmware_id
    with requests.get(fetch_url, stream=True, headers=headers) as response:
        resp_dict = response.json()
        object_id_list = ""
    return object_id_list


def authenticate(url, username, password):
    auth_url = url + f'/#query=query%20MyQuery%20%7B%0A%20%20tokenAuth(password%3A%20"{password}"%2C%20username%3A%20' \
                f'"{username}")%20%7B%0A%20%20%20%20token%0A%20%20%7D%0A%7D&operationName=MyQuery'
    with requests.get(auth_url, stream=True) as response:
        resp_dict = response.json()
        jwt_token = resp_dict["data"]["tokenAuth"]["token"]
    return jwt_token


def main():
    parser = argparse.ArgumentParser(prog='fmd_build_injector',
                                     description="A cli tool to download and store build files from FirmwareDroid.")

    parser.add_argument("-r", "--read", type=str, nargs=1,
                        metavar="file_name", default=None,
                        help="Opens and reads the specified text file.")
    parser.add_argument("-u", "--url", type=str, nargs=1, metavar="t", default=None, required=True,
                        help="HTTP/HTTPS url to the FirmwareDroid instance. "
                             "Example: https://firmwaredroid.cloudlab.zhaw.ch")
    parser.add_argument("-a", "--account", type=str, nargs=1, default=None, required=True,
                        help="Username for JWT authentication.")
    parser.add_argument("-o", "--output", type=str, nargs=1, default=None, required=True,
                        help="Destination path to store the files. For every apk a new subfolder will be created.")
    parser.add_argument("-f", "--firmware_id", type=str, nargs=1, default=None, required=True,
                        help="Specify the document object id for the firmware to prepare.")
    args = parser.parse_args()

    if not args.url.startswith("https://") or not args.url.startswith("http://"):
        exit(1)

    password = getpass()
    jwt_token = authenticate(args.url, args.username, password)

    object_id_list = get_app_list(args.url, jwt_token, args.firmware_id)
    for object_id in tqdm(object_id_list):
        file_path = download_zip(args.url, object_id, jwt_token, args.output)
        extract_zip(file_path, args.output)


if __name__ == "__main__":
    # calling the main function
    main()
