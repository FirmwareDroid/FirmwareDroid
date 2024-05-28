SHARED_LIBRARY_MODULE_TEMPLATE = "LOCAL_PATH := $$(call my-dir)\n" \
                                 "\ninclude $$(CLEAR_VARS)\n" \
                                 "\nLOCAL_MODULE := ${local_module}\n" \
                                 "\nLOCAL_SRC_FILES := ${local_src_files}\n" \
                                 "\nLOCAL_MODULE_CLASS := SHARED_LIBRARIES\n" \
                                 "\nLOCAL_MODULE_SUFFIX := .so\n" \
                                 "\nLOCAL_PREBUILT_MODULE_FILE := $(LOCAL_SRC_FILES)\n" \
                                 "\ninclude $$(PREBUILT_SHARED_LIBRARY)\n"

# libs/$(TARGET_ARCH_ABI)/libmy_prebuilt_lib.so
