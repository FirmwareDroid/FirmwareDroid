ANDROID_MK_SHARED_LIBRARY_TEMPLATE = "LOCAL_PATH := $$(call my-dir)\n" \
                                     "\ninclude $$(CLEAR_VARS)\n" \
                                     "\nLOCAL_MODULE := ${local_module}\n" \
                                     "\nLOCAL_SRC_FILES := ${local_src_files}\n" \
                                     "\nLOCAL_MODULE_CLASS := SHARED_LIBRARIES\n" \
                                     "\nLOCAL_MODULE_SUFFIX := .so\n" \
                                     "\nLOCAL_MODULE_TAGS := optional\n" \
                                     "\nLOCAL_MODULE_PATH := ${local_module_path}\n" \
                                     "\nLOCAL_PREBUILT_MODULE_FILE := ${local_prebuilt_module_file}\n" \
                                     "\n#$$(LOCAL_MODULE_PATH):\n" \
                                     "\t#$$(hide) mkdir -p '${local_module_path}'\n" \
                                     "\n$$(LOCAL_INSTALLED_MODULE): $$(LOCAL_MODULE_PATH)\n" \
                                     "\ninclude $$(PREBUILT_SHARED_LIBRARY)\n"



# prebuilt_shared_library: This defines a prebuilt shared library in the Android.bp system. It is equivalent to LOCAL_MODULE := ${local_module} and LOCAL_MODULE_CLASS := SHARED_LIBRARIES in Android.mk.
# name: This is the module name (LOCAL_MODULE in Android.mk).
# srcs: This lists the source files (equivalent to LOCAL_SRC_FILES in Android.mk).
# tag: Defines the module tags, similar to LOCAL_MODULE_TAGS. It can be adjusted based on your needs, such as optional.
# suffix: Sets the file extension (.so) for shared libraries, which corresponds to LOCAL_MODULE_SUFFIX in Android.mk.
# path: Specifies where the prebuilt module should be placed, similar to LOCAL_MODULE_PATH.
# export_include_dirs: This is optional and defines where the include directories for the shared library are. If needed, you can specify the paths relative to the module's directory.
# whole_archive: This is an optional property you can include if you want to include all the object files in the prebuilt shared library (like LOCAL_INSTALLED_MODULE in Android.mk).
# prebuilt and existing: These properties indicate that the module is a prebuilt shared library and that it already exists.
# static_libs: If the shared library depends on static libraries, you can specify them here.
ANDROID_BP_SHARED_LIBRARY_TEMPLATE = """
cc_prebuilt_library_shared {
    name: "${local_module}",\n
    srcs: ["${local_src_files}"],\n
    tag: "optional",\n
    suffix: ".so",\n
    path: "${local_module_path}",\n
    export_include_dirs: [""],
    whole_archive: true,\n
    prebuilt: true,\n
    existing: true,\n
    static_libs: [""],\n 
    apex_available: [""],
}
"""
