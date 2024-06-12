ANDROID_MK_JAVA_MODULE_TEMPLATE = "LOCAL_PATH := $$(call my-dir)\n" + \
                                  "include $$(CLEAR_VARS)\n" + \
                                  "LOCAL_MODULE := ${local_module}\n" + \
                                  "LOCAL_MODULE_CLASS := JAVA_LIBRARIES\n" + \
                                  "LOCAL_SRC_FILES := ${local_src_files}\n" + \
                                  "LOCAL_OVERRIDES_PACKAGES := framework\n" + \
                                  "LOCAL_MODULE_PATH := ${local_module_path}\n" + \
                                  "include $$(BUILD_PREBUILT)\n"
