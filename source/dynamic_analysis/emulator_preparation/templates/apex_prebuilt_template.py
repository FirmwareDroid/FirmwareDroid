APEX_PREBUILT_TEMPLATE = "prebuilt_apex {\n" \
                         "name: \"${apex_name}\",\n" \
                         "overrides: [],\n" \
                         "arch: {\n" \
                         "arm64: {src: \"${apex_relative_path_arm64}\",},\n" \
                         "x86_64: {src: \"${apex_relative_path_x86_x64}\",},\n" \
                         "},\n" \
                         "filename: \"${apex_filename}\",\n" \
                         "prefer: true,\n" \
                         "installable: true\n" \
                         "}"
