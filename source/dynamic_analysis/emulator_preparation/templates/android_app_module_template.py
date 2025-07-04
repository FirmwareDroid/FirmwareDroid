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
                      "\nLOCAL_MODULE_RELATIVE_PATH := ${local_module_relative_path}\n" \
                      "\nLOCAL_OVERRIDES_PACKAGES := ${local_overrides_packages}\n" \
                      "\ninclude $$(BUILD_PREBUILT)\n"

#    relative_install_path: "${local_module_relative_path}",
#     vendor: ${vendor},
ANDROID_BP_TEMPLATE = """
android_app_import {
    name: "${local_module}", 
    apk: "${local_src_files}",
    certificate: "${local_certificate}",
    privileged: ${local_privileged_module},
    filename: "${local_filename}",
    presigned: false,
    dex_preopt: {
        enabled: false,
    },
    optional_uses_libs: [${local_optional_uses_libraries}],
    enforce_uses_libs: ${local_enforce_uses_libraries},
    overrides: ["${local_overrides}"],
    prefer: true,
    product_specific: ${product_specific},
    proprietary: ${proprietary},
   
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
    "Tethering",                 # com.android.networkstack.tethering
]


AOSP_DEFAULT_PACKAGE_NAMES = ["BasicDreams",
                              "SimAppDialog",
                              "WallpaperBackup",
                              "KeyChain",
                              "PacProcessor",
                              "HTMLViewer",
                              "Stk",
                              "PrintSpooler",
                              "PartnerBookmarksProvider",
                              "CameraExtensionsProxy",
                              "PrintRecommendationService",
                              "CaptivePortalLogin",
                              "EasterEgg",
                              "CarrierDefaultApp",
                              "ExtShared",
                              "CertInstaller",
                              "BookmarkProvider",
                              "CompanionDeviceManager",
                              "BluetoothMidiService",
                              "Bluetooth",
                              "NfcNci",
                              "MmsService",
                              "TeleService",
                              "ProxyHandler",
                              "MusicFX",
                              "InputDevices",
                              "Tag",
                              "BuiltInPrintService",
                              "PackageInstaller",
                              "Traceur",
                              "LocalTransport",
                              "ManagedProvisioning",
                              "NetworkPermissionConfig",
                              "SettingsProvider",
                              "DocumentsUI",
                              "ONS",
                              "Telecom",
                              "CallLogBackup",
                              "DownloadProvider",
                              "StatementService",
                              "ContactsProvider",
                              "FusedLocation",
                              "NetworkStack",
                              "DownloadProviderUi",
                              "Shell",
                              "BlockedNumberProvider",
                              "MtpService",
                              "DynamicSystemInstallationService",
                              "CalendarProvider",
                              "UserDictionaryProvider",
                              "CellBroadcastLegacyApp",
                              "VpnDialogs",
                              "TelephonyProvider",
                              "SharedStorageBackup",
                              "MediaProviderLegacy",
                              "SoundPicker",
                              "ExternalStorageProvider",
                              "SecureElement",
                              "LiveWallpapersPicker",
                              "Browser2",
                              "CarrierConfig",
                              "DeskClock",
                              "EmergencyInfo",
                              "ImsServiceEntitlement",
                              "ManagedProvisioning",
                              "Nfc",
                              "Protips",
                              "RemoteProvisioner",
                              "Settings",
                              "StorageManager",
                              "ThemePicker",
                              "TvSettings",
                              "Calendar",
                              "CellBroadcastReceiver",
                              "DevCamera",
                              "Gallery",
                              "KeyChain",
                              "Messaging",
                              "OnDeviceAppPrediction",
                              "Provision",
                              "SafetyRegulatoryInfo",
                              "SettingsIntelligence",
                              "TV",
                              "TimeZoneData",
                              "UniversalMediaPlayer",
                              "BasicSmsReceiver",
                              "Camera2",
                              "CertInstaller",
                              "Dialer",
                              "Gallery2",
                              "Launcher3",
                              "Music",
                              "OneTimeInitializer",
                              "QuickAccessWallet",
                              "SampleLocationAttribution",
                              "SpareParts",
                              "Tag",
                              "TimeZoneUpdater",
                              "WallpaperPicker",
                              "Bluetooth",
                              "Car",
                              "Contacts",
                              "DocumentsUI",
                              "HTMLViewer",
                              "LegacyCamera",
                              "MusicFX",
                              "PhoneCommon",
                              "QuickSearchBox",
                              "SecureElement",
                              "Stk",
                              "Test",
                              "Traceur",
                              "WallpaperPicker2",
                              "BackupRestoreConfirmation",
                              "BasicDreams",
                              "CellBroadcastServiceModulePlatform",
                              "CtsShim",
                              "CtsShimPriv",
                              "InProcessNetworkStack",
                              "MediaProvider",
                              "ImageWallpaper",
                              "LivePicker",
                              "AlternativeNetworkAccess",
                              "Iwlan",
                              "PlatformCaptivePortalLogin",
                              "PermissionController",
                              "PlatformNetworkPermissionConfig",
                              "Provision",
                              "PhotoTable",
                              "SystemUI",
                              "WallpaperCropper",
                              "SettingsLib",
                              "WindowManager",
                              "AppPredictionLib",
                              "Keyguard",
                              "WAPPushManager",
                              "Backup",
                              "FakeOemFeatures",
                              "BackupEncryption",
                              "EncryptedLocalTransport",
                              "MtpDocumentsProvider",
                              "ModuleMetadata",
                              "ExtServices",
                              "CarrierDefaultApp",
                              "ANGLE"]