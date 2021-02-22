from model import BuildPropFile


class BuildPropParser:
    def __init__(self, build_prop_file_path):
        self.build_prop_file_path = build_prop_file_path
        self.properties = {}
        self.parse_props()

    def parse_props(self):
        """Creates a dict from all properties available in the build.prop file. """
        with open(self.build_prop_file_path, "rb") as f:
            for line in f:
                line = line.decode('utf-8')
                line = line.rstrip()
                if line:
                    line_split_list = line.split("=")
                    if len(line_split_list) == 2:
                        key = line_split_list[0].replace(".", "_")
                        value = line_split_list[1]
                        self.properties[key] = value

    def create_build_prop_document(self):
        """ Creates a db document of the build prop file. """
        build_prop_file = open(self.build_prop_file_path, "rb")
        build_prop = BuildPropFile(build_prop_file=build_prop_file.read(),
                                   properties=self.properties)
        build_prop_file.close()
        return build_prop
