ANDROID_MK_JAVA_MODULE_TEMPLATE = "LOCAL_PATH := $$(call my-dir)\n" + \
                                  "include $$(CLEAR_VARS)\n" + \
                                  "LOCAL_SRC_FILES := ${local_src_files}\n" + \
                                  "LOCAL_MODULE := ${local_module}\n" + \
                                  "LOCAL_MODULE_CLASS := ETC\n" + \
                                  "LOCAL_MODULE_TAGS := optional\n" + \
                                  "LOCAL_MODULE_SUFFIX := .jar\n" + \
                                  "LOCAL_DEX_PREOPT := false\n" + \
                                  "LOCAL_PRIVILEGED_MODULE := true\n" + \
                                  "LOCAL_MODULE_PATH := ${local_module_path}\n" + \
                                  "LOCAL_ENFORCE_USES_LIBRARIES := false\n" + \
                                  "\n$$(LOCAL_MODULE_PATH):\n" \
                                  "\t$$(hide) mkdir -p '${local_module_path}'\n" \
                                  "\n$$(LOCAL_INSTALLED_MODULE): ${local_module_path}\n" \
                                   "LOCAL_POST_INSTALL_CMD := $$(hide) " \
                                   "$$(LOCAL_PATH)/replacer.sh ${local_module_path}${local_scr_file_out} " \
                                   "${local_module_path}${local_src_files}\n" + \
                                  "include $$(BUILD_PREBUILT)\n"
