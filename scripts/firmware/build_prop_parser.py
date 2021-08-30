# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
from model import BuildPropFile


class BuildPropParser:
    def __init__(self, firmware_file):
        self.firmware_file = firmware_file
        self.build_prop_file_path = firmware_file.absolute_store_path
        self.properties = {}
        self.parse_props()

    def parse_props(self):
        """Creates a dict from all properties available in the build.prop file. """
        with open(self.build_prop_file_path, "rb") as f:
            for line in f:
                line = line.decode('utf-8')
                line = line.rstrip()
                if line:
                    # TODO Add code to follow @import statements in build.prop file
                    line_split_list = line.split("=")
                    if len(line_split_list) == 2:
                        key = line_split_list[0].replace(".", "_")
                        value = line_split_list[1]
                        if value is None:
                            value = "null"
                        self.properties[key] = value

    def create_build_prop_document(self):
        """ Creates a db document of the build prop file. """
        build_prop_file = open(self.build_prop_file_path, "rb")
        if self.properties is {}:
            self.properties["error"] = "could not parse build.prop properties"
        build_prop = BuildPropFile(build_prop_file=build_prop_file.read(),
                                   firmware_file_id_reference=self.firmware_file.id,
                                   properties=self.properties).save()
        build_prop_file.close()
        return build_prop
