import os

META_BUILD_FILENAME_SYSTEM = "meta_build_system.txt"
META_BUILD_FILENAME_VENDOR = "meta_build_vendor.txt"
META_BUILD_FILENAME_PRODUCT = "meta_build_product.txt"


def add_module_to_meta_file(partition_name, tmp_root_dir, module_naming):
    """
    Writes the module naming to a meta file for the given Android app.

    :param partition_name: str - The partition name of the app.
    :param tmp_root_dir: str - A temporary directory to store the build files.
    :param module_naming: str - A string to name the module in the build file.

    :return:
    """

    if partition_name.lower() == "vendor" or partition_name.lower() == "oem" or partition_name.lower() == "odm":
        meta_file = os.path.join(tmp_root_dir, META_BUILD_FILENAME_VENDOR)
    elif partition_name.lower() == "product":
        meta_file = os.path.join(tmp_root_dir, META_BUILD_FILENAME_PRODUCT)
    else:
        meta_file = os.path.join(tmp_root_dir, META_BUILD_FILENAME_SYSTEM)

    with open(meta_file, 'a') as fp:
        fp.write("    " + module_naming + " \\\n")
