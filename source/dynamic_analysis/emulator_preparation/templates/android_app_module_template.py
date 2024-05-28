ANDROID_MK_TEMPLATE = "LOCAL_PATH := $$(call my-dir)\n" \
                      "\ninclude $$(CLEAR_VARS)\n" \
                      "\nLOCAL_MODULE_TAGS := optional \n" \
                      "\nLOCAL_MODULE := ${local_module}\n" \
                      "\nLOCAL_MODULE_PATH := ${local_module_path}\n" \
                      "\nLOCAL_CERTIFICATE := ${local_certificate}\n" \
                      "\nLOCAL_SRC_FILES := ${local_src_files}\n" \
                      "\nLOCAL_MODULE_CLASS := APPS\n" \
                      "\nLOCAL_MODULE_SUFFIX := $$(COMMON_ANDROID_PACKAGE_SUFFIX)\n" \
                      "\nLOCAL_OPTIONAL_USES_LIBRARIES := ${local_optional_uses_libraries}\n" \
                      "\nLOCAL_ENFORCE_USES_LIBRARIES := ${local_enforce_uses_libraries}\n" \
                      "\nLOCAL_DEX_PREOPT := ${local_dex_preopt}\n" \
                      "\nLOCAL_PRIVILEGED_MODULE := ${local_privileged_module}\n" \
                      "\ninclude $$(BUILD_PREBUILT)\n"

ANDROID_BP_TEMPLATE = ""
