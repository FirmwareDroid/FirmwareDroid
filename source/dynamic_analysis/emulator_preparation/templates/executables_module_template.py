ANDROID_MK_EXECUTABLE_MODULE_TEMPLATE = "LOCAL_PATH := $$(call my-dir)\n" + \
                                        "include $$(CLEAR_VARS)\n" + \
                                        "LOCAL_MODULE := ${local_module}\n" + \
                                        "LOCAL_MODULE_PATH := ${local_module_path}\n" + \
                                        "LOCAL_MODULE_CLASS := ETC\n" + \
                                        "LOCAL_MODULE_SUFFIX := \n" + \
                                        "LOCAL_PRIVILEGED_MODULE := true\n" + \
                                        "#$$(LOCAL_MODULE_PATH):\n" \
                                        "#\t$$(hide) mkdir -p '${local_module_path}'\n" \
                                        "$$(LOCAL_INSTALLED_MODULE): ${local_module_path}\n" \
                                        "include $$(BUILD_PREBUILT)\n"
