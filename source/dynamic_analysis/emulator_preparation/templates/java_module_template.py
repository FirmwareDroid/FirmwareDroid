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
                                  "BASE_PATH=$$(pwd | sed 's|\\(/frameworks/.*\\)||')\n" + \
                                  "TARGET_OUT_ABS=$$(BASE_PATH)/${local_module_path}\n" + \
                                  ("LOCAL_POST_INSTALL_CMD := $$(hide) "
                                   "$$(LOCAL_PATH)/replacer.sh $$(TARGET_OUT_ABS)/${local_src_files_target} "
                                   "$$(TARGET_OUT_ABS)/${local_src_files}\n") + \
                                  "include $$(BUILD_PREBUILT)\n"
