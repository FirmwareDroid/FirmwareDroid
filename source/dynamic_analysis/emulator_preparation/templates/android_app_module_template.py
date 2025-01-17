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

ANDROID_BP_TEMPLATE = """
prebuilt_apk {\n
    name: "${local_module}", \n
    src: "${local_src_files}",\n
    certificate: "${local_certificate}",\n
    privileged: ${local_privileged_module},\n
    dex_preopt: {\n
        enabled: false,\n
    },\n
    optional_uses_libs: [${local_optional_uses_libraries}],\n
    enforce_uses_libs: ${local_enforce_uses_libraries},\n
    installable: true,\n
    tags: ["optional"],\n
    overrides: ["${local_overrides}"],\n
}
"""


LIST_SINGLETON_APP_MODULES = [
    "PackageInstaller",          # com.android.packageinstaller
    "SystemUI",                  # com.android.systemui
    "Settings",                  # com.android.settings
    "Telecom",                   # com.android.server.telecom
    "ContactsProvider",          # com.android.providers.contacts
    "MediaProvider",             # com.android.providers.media
    "PermissionController",      # com.android.permissioncontroller
    "LatinIME",                  # com.android.inputmethod.latin
    "Dialer",                    # com.android.dialer
    "NetworkStack",              # com.android.networkstack
]
