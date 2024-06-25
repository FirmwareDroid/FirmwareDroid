ANDROID_MK_SHARED_LIBRARY_TEMPLATE = "LOCAL_PATH := $$(call my-dir)\n" \
                                     "\ninclude $$(CLEAR_VARS)\n" \
                                     "\nLOCAL_MODULE := ${local_module}\n" \
                                     "\nLOCAL_SRC_FILES := ${local_src_files}\n" \
                                     "\nLOCAL_MODULE_CLASS := SHARED_LIBRARIES\n" \
                                     "\nLOCAL_MODULE_SUFFIX := .so\n" \
                                     "\nLOCAL_MODULE_TAGS := optional\n" \
                                     "\nLOCAL_MODULE_PATH := ${local_module_path}\n" \
                                     "\nLOCAL_PREBUILT_MODULE_FILE := ${local_prebuilt_module_file}\n" \
                                     "\n$$(LOCAL_MODULE_PATH):\n" \
                                     "\t$$(hide) mkdir -p '${local_module_path}'\n" \
                                     "\n$$(LOCAL_INSTALLED_MODULE): $$(LOCAL_MODULE_PATH)\n" \
                                     "\ninclude $$(PREBUILT_SHARED_LIBRARY)\n"

ANDROID_BP_SHARED_LIBRARY_TEMPLATE = "cc_library_shared {\n" \
                                     "    name: \"${local_module}\",\n" \
                                     "    srcs: [\"${local_src_files}\"],\n" \
                                     "    shared_libs: [],\n" \
                                     "    export_shared_lib_headers: [],\n" \
                                     "    export_include_dirs: [],\n" \
                                     "    export_system_include_dirs: [],\n" \
                                     "    export_local_include_dirs: [],\n" \
                                     "    export_generated_include_dirs: [],\n" \
                                     "    export_generated_headers: [],\n" \
                                     "    target: {\n" \
                                     "        android: {\n" \
                                     "            srcs: [\"${local_src_files}\"],\n" \
                                     "        },\n" \
                                     "    },\n" \
                                     "    stl: \"none\",\n" \
                                     "    arch: {\n" \
                                     "        arm64: {\n" \
                                     "            srcs: [\"${local_src_files}\"],\n" \
                                     "        },\n" \
                                     "        x86_64: {\n" \
                                     "            srcs: [\"${local_src_files}\"],\n" \
                                     "        },\n" \
                                     "    },\n" \
                                     "}\n"
