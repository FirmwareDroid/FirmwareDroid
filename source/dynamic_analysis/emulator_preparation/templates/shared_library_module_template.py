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

ANDROID_BP_SHARED_LIBRARY_TEMPLATE = """
cc_prebuilt_library_shared {
    name: "${local_module}",
    srcs: ["${local_src_files}"],
    stem: "${stem_name}",
    prefer: true,
    overrides: ["${local_overrides}"],
    check_elf_files: false,
    stl: "none",
    system_shared_libs: [],
    apex_available: ["//apex_available:anyapex", "//apex_available:platform"],
}
"""


AOSP_12_SHARED_LIBRARIES = [
    "aaudio-aidl-cpp",
    "android.frameworks.bufferhub@1.0",
    "android.frameworks.cameraservice.common@2.0",
    "android.frameworks.cameraservice.device@2.0",
    "android.frameworks.cameraservice.device@2.1",
    "android.frameworks.cameraservice.service@2.0",
    "android.frameworks.cameraservice.service@2.1",
    "android.frameworks.cameraservice.service@2.2",
    "android.frameworks.displayservice@1.0",
    "android.frameworks.schedulerservice@1.0",
    "android.frameworks.sensorservice@1.0",
    "android.frameworks.stats-V1-ndk_platform",
    "android.frameworks.stats@1.0",
    "android.hardware.atrace@1.0",
    "android.hardware.audio.common-util",
    "android.hardware.audio.common@2.0",
    "android.hardware.audio.common@4.0-util",
    "android.hardware.audio.common@4.0",
    "android.hardware.audio.common@5.0-util",
    "android.hardware.audio.common@5.0",
    "android.hardware.audio.common@6.0-util",
    "android.hardware.audio.common@6.0",
    "android.hardware.audio.common@7.0-enums",
    "android.hardware.audio.common@7.0-util",
    "android.hardware.audio.common@7.0",
    "android.hardware.audio.effect@4.0-util",
    "android.hardware.audio.effect@4.0",
    "android.hardware.audio.effect@5.0-util",
    "android.hardware.audio.effect@5.0",
    "android.hardware.audio.effect@6.0-util",
    "android.hardware.audio.effect@6.0",
    "android.hardware.audio.effect@7.0-util",
    "android.hardware.audio.effect@7.0",
    "android.hardware.audio@4.0-util",
    "android.hardware.audio@4.0",
    "android.hardware.audio@5.0-util",
    "android.hardware.audio@5.0",
    "android.hardware.audio@6.0-util",
    "android.hardware.audio@6.0",
    "android.hardware.audio@7.0-util",
    "android.hardware.audio@7.0",
    "android.hardware.biometrics.fingerprint@2.1",
    "android.hardware.bluetooth.a2dp@1.0",
    "android.hardware.bluetooth.audio@2.0",
    "android.hardware.bluetooth.audio@2.1",
    "android.hardware.bluetooth@1.0",
    "android.hardware.bluetooth@1.1",
    "android.hardware.boot@1.0",
    "android.hardware.boot@1.1",
    "android.hardware.boot@1.2",
    "android.hardware.broadcastradio@1.0",
    "android.hardware.broadcastradio@1.1",
    "android.hardware.camera.common@1.0",
    "android.hardware.camera.device@1.0",
    "android.hardware.camera.device@3.2",
    "android.hardware.camera.device@3.3",
    "android.hardware.camera.device@3.4",
    "android.hardware.camera.device@3.5",
    "android.hardware.camera.device@3.6",
    "android.hardware.camera.device@3.7",
    "android.hardware.camera.metadata@3.2",
    "android.hardware.camera.metadata@3.3",
    "android.hardware.camera.metadata@3.4",
    "android.hardware.camera.metadata@3.5",
    "android.hardware.camera.metadata@3.6",
    "android.hardware.camera.provider@2.4",
    "android.hardware.camera.provider@2.5",
    "android.hardware.camera.provider@2.6",
    "android.hardware.camera.provider@2.7",
    "android.hardware.cas.native@1.0",
    "android.hardware.cas@1.0",
    "android.hardware.common-V2-ndk_platform",
    "android.hardware.configstore-utils",
    "android.hardware.configstore@1.0",
    "android.hardware.configstore@1.1",
    "android.hardware.confirmationui@1.0",
    "android.hardware.contexthub@1.0",
    "android.hardware.drm@1.0",
    "android.hardware.drm@1.1",
    "android.hardware.drm@1.2",
    "android.hardware.drm@1.3",
    "android.hardware.drm@1.4",
    "android.hardware.dumpstate@1.0",
    "android.hardware.dumpstate@1.1",
    "android.hardware.gatekeeper@1.0",
    "android.hardware.gnss-V1-cpp",
    "android.hardware.gnss.measurement_corrections@1.0",
    "android.hardware.gnss.visibility_control@1.0",
    "android.hardware.gnss.measurement_corrections@1.1",
    "android.hardware.gnss@1.0",
    "android.hardware.gnss@1.1",
    "android.hardware.gnss@2.0",
    "android.hardware.gnss@2.1",
    "android.hardware.graphics.allocator@2.0",
    "android.hardware.graphics.allocator@3.0",
    "android.hardware.graphics.allocator@4.0",
    "android.hardware.graphics.bufferqueue@1.0",
    "android.hardware.graphics.bufferqueue@2.0",
    "android.hardware.graphics.common-V2-ndk_platform",
    "android.hardware.graphics.common@1.0",
    "android.hardware.graphics.common@1.1",
    "android.hardware.graphics.common@1.2",
    "android.hardware.graphics.composer@2.1",
    "android.hardware.graphics.composer@2.2",
    "android.hardware.graphics.composer@2.3",
    "android.hardware.graphics.composer@2.4",
    "android.hardware.graphics.mapper@2.0",
    "android.hardware.graphics.mapper@2.1",
    "android.hardware.graphics.mapper@3.0",
    "android.hardware.graphics.mapper@4.0",
    "android.hardware.health.storage-V1-ndk_platform",
    "android.hardware.health.storage@1.0",
    "android.hardware.health@1.0",
    "android.hardware.health@2.0",
    "android.hardware.health@2.1",
    "android.hardware.identity-support-lib",
    "android.hardware.input.classifier@1.0",
    "android.hardware.input.common@1.0",
    "android.hardware.ir@1.0",
    "android.hardware.keymaster@3.0",
    "android.hardware.keymaster@4.0",
    "android.hardware.keymaster@4.1",
    "android.hardware.light@2.0",
    "android.hardware.media.bufferpool@2.0",
    "android.hardware.media.c2@1.0",
    "android.hardware.media.c2@1.1",
    "android.hardware.media.c2@1.2",
    "android.hardware.media.omx@1.0",
    "android.hardware.media@1.0",
    "android.hardware.memtrack-V1-ndk_platform",
    "android.hardware.memtrack@1.0",
    "android.hardware.nfc@1.0",
    "android.hardware.nfc@1.1",
    "android.hardware.nfc@1.2",
    "android.hardware.power-V1-cpp",
    "android.hardware.power-V2-cpp",
    "android.hardware.power.stats-V1-cpp",
    "android.hardware.power.stats-V1-ndk_platform",
    "android.hardware.power.stats@1.0",
    "android.hardware.power@1.0",
    "android.hardware.power@1.1",
    "android.hardware.power@1.2",
    "android.hardware.power@1.3",
    "android.hardware.radio.config@1.0",
    "android.hardware.radio.deprecated@1.0",
    "android.hardware.radio@1.0",
    "android.hardware.radio@1.1",
    "android.hardware.radio@1.2",
    "android.hardware.radio@1.3",
    "android.hardware.radio@1.4",
    "android.hardware.renderscript@1.0",
    "android.hardware.secure_element@1.0",
    "android.hardware.security.keymint-V1-cpp",
    "android.hardware.security.keymint-V1-ndk_platform",
    "android.hardware.security.secureclock-V1-cpp",
    "android.hardware.security.secureclock-V1-ndk_platform",
    "android.hardware.security.sharedsecret-V1-ndk_platform",
    "android.hardware.sensors@1.0",
    "android.hardware.sensors@2.0",
    "android.hardware.sensors@2.1",
    "android.hardware.thermal@1.0",
    "android.hardware.tv.input@1.0",
    "android.hardware.usb.gadget@1.0",
    "android.hardware.vibrator-V2-cpp",
    "android.hardware.vibrator-V2-ndk_platform",
    "android.hardware.vibrator@1.0",
    "android.hardware.vibrator@1.1",
    "android.hardware.vibrator@1.2",
    "android.hardware.vibrator@1.3",
    "android.hardware.vr@1.0",
    "android.hardware.wifi@1.0",
    "android.hidl.allocator@1.0",
    "android.hidl.memory.token@1.0",
    "android.hidl.memory@1.0",
    "android.hidl.safe_union@1.0",
    "android.hidl.token@1.0-utils",
    "android.hidl.token@1.0",
    "android.security.apc-ndk_platform",
    "android.security.authorization-ndk_platform",
    "android.security.compat-ndk_platform",
    "android.security.legacykeystore-ndk_platform",
    "android.security.maintenance-ndk_platform",
    "android.system.keystore2-V1-cpp",
    "android.system.keystore2-V1-ndk_platform",
    "android.system.net.netd@1.0",
    "android.system.net.netd@1.1",
    "android.system.suspend.control-V1-cpp",
    "android.system.suspend.control-V1-ndk",
    "android.system.suspend.control.internal-cpp",
    "android.system.suspend@1.0",
    "android.system.wifi.keystore@1.0",
    "apex_aidl_interface-cpp",
    "audio_common-aidl-cpp",
    "audioclient-types-aidl-cpp",
    "audioflinger-aidl-cpp",
    "audiopolicy-aidl-cpp",
    "audiopolicy-types-aidl-cpp",
    "av-types-aidl-cpp",
    "capture_state_listener-aidl-cpp",
    "dnsresolver_aidl_interface-V7-cpp",
    "drm/libfwdlockengine",
    "effect-aidl-cpp",
    "framework-permission-aidl-cpp",
    "gsi_aidl_interface-cpp",
    "heapprofd_client",
    "heapprofd_client_api",
    "hw/android.hidl.memory@1.0-impl",
    "hw/audio.a2dp.default",
    "hw/audio.hearing_aid.default",
    "ld-android",
    "lib-platform-compat-native-api",
    "libEGL",
    "libETC1",
    "libFFTEm",
    "libGLESv1_CM",
    "libGLESv2",
    "libGLESv3",
    "libInputFlingerProperties",
    "libLLVM_android",
    "libOpenMAXAL",
    "libOpenSLES",
    "libRS",
    "libRSCacheDir",
    "libRSCpuRef",
    "libRSDriver",
    "libRS_internal",
    "libRScpp",
    "libSurfaceFlingerProp",
    "libSuspendProperties",
    "lib_android_keymaster_keymint_utils",
    "libaaudio",
    "libaaudio_internal",
    "libaaudioservice",
    "libactivitymanager_aidl",
    "libadbd_auth",
    "libadbd_fs",
    "libalarm_jni",
    "libamidi",
    "libandroid",
    "libandroid_log_sys.dylib",
    "libandroid_logger.dylib",
    "libandroid_net",
    "libandroid_runtime",
    "libandroid_runtime_lazy",
    "libandroid_servers",
    "libandroidfw",
    "libanyhow.dylib",
    "libappfuse",
    "libartpalette-system",
    "libasyncio",
    "libaudio-resampler",
    "libaudioclient",
    "libaudioclient_aidl_conversion",
    "libaudioeffect_jni",
    "libaudioflinger",
    "libaudiofoundation",
    "libaudiohal",
    "libaudiohal@4.0",
    "libaudiohal@5.0",
    "libaudiohal@6.0",
    "libaudiohal@7.0",
    "libaudiohal_deathhandler",
    "libaudiomanager",
    "libaudiopolicy",
    "libaudiopolicyengineconfigurable",
    "libaudiopolicyenginedefault",
    "libaudiopolicymanagerdefault",
    "libaudiopolicyservice",
    "libaudioprocessing",
    "libaudiospdif",
    "libaudioutils",
    "libavservices_minijail",
    "libbacktrace",
    "libbase",
    "libbatterystats_aidl",
    "libbcc",
    "libbcinfo",
    "libbinder",
    "libbinder_ndk",
    "libbinder_ndk_sys.dylib",
    "libbinder_rs.dylib",
    "libbinderdebug",
    "libbinderwrapper",
    "libblas",
    "libbluetooth",
    "libbluetooth_jni",
    "libbootanimation",
    "libbootloader_message",
    "libbpf",
    "libbpf_android",
    "libbrillo-binder",
    "libbrillo-stream",
    "libbrillo",
    "libbufferhub",
    "libbufferhubqueue",
    "libbyteorder.dylib",
    "libc++",
    "libc",
    "libcamera2ndk",
    "libcamera_client",
    "libcamera_metadata",
    "libcameraservice",
    "libcap",
    "libcfg_if.dylib",
    "libcgrouprc",
    "libchrome",
    "libchrono.dylib",
    "libclang_rt.asan-aarch64-android",
    "libclang_rt.ubsan_standalone-aarch64-android",
    "libcodec2",
    "libcodec2_client",
    "libcodec2_hidl_client@1.0",
    "libcrypto",
    "libcodec2_hidl_client@1.1",
    "libcodec2_hidl_client@1.2",
    "libcodec2_vndk",
    "libcompiler_rt",
    "libcppbor_external",
    "libcppcose_rkp",
    "libcrc32fast.dylib",
    "libcredstore_aidl",
    "libcrypto_utils",
    "libcups",
    "libcurl",
    "libcutils",
    "libdataloader",
    "libdatasource",
    "libdebuggerd_client",
    "libdiskconfig",
    "libdisplayservicehidl",
    "libdl",
    "libdl_android",
    "libdmabufheap",
    "libdng_sdk",
    "libdrm",
    "libdrmframework",
    "libdrmframework_jni",
    "libdrmframeworkcommon",
    "libdumpstateaidl",
    "libdumpstateutil",
    "libdumputils",
    "libdynamic_depth",
    "libeffectsconfig",
    "libenv_logger.dylib",
    "libevent",
    "libexif",
    "libexpat",
    "libext2_blkid",
    "libext2_com_err",
    "libext2_e2p",
    "libext2_misc",
    "libext2_quota",
    "libext2_uuid",
    "libext2fs",
    "libext4_utils",
    "libf2fs_sparseblock",
    "libfdtrack",
    "libfec",
    "libfilterfw",
    "libfilterpack_imageproc",
    "libflatbuffers-cpp",
    "libflate2.dylib",
    "libfmq",
    "libfruit",
    "libfs_mgr",
    "libfs_mgr_binder",
    "libfsverity",
    "libft2",
    "libgatekeeper",
    "libgatekeeper_aidl",
    "libgetrandom.dylib",
    "libgfxstats",
    "libgpumem",
    "libgpumemtracer",
    "libgpuservice",
    "libgralloctypes",
    "libgraphicsenv",
    "libgrpc++",
    "libgrpc_wrap",
    "libgsi",
    "libgui",
    "libhardware",
    "libhardware_legacy",
    "libharfbuzz_ng",
    "libheadtracking-binding",
    "libheadtracking",
    "libheif",
    "libhidcommand_jni",
    "libhidl-gen-hash",
    "libhidl-gen-utils",
    "libhidlallocatorutils",
    "libhidlbase",
    "libhidlmemory",
    "libhidltransport",
    "libhwbinder",
    "libhwui",
    "libidmap2",
    "libidmap2_policies",
    "libimage_io",
    "libimg_utils",
    "libincfs",
    "libincident",
    "libincidentpriv",
    "libinput",
    "libinputflinger",
    "libinputflinger_base",
    "libinputreader",
    "libinputreporter",
    "libinputservice",
    "libion",
    "libiprouteutil",
    "libitoa.dylib",
    "libjnigraphics",
    "libjpeg",
    "libjsoncpp",
    "libkeymaster4_1support",
    "libkeymaster4support",
    "libkeymaster_messages",
    "libkeymaster_portable",
    "libkeymint",
    "libkeymint_support",
    "libkeystore-attestation-application-id",
    "libkeystore-engine",
    "libkeystore2_aaid",
    "libkeystore2_apc_compat",
    "libkeystore2_crypto",
    "libkeystore2_vintf_cpp",
    "libkeyutils",
    "libkll",
    "libkm_compat",
    "libkm_compat_service",
    "liblayers_proto",
    "liblazy_static.dylib",
    "libldacBT_abr",
    "libldacBT_enc",
    "liblibc.dylib",
    "liblibprofcollectd.dylib",
    "liblibz_sys.dylib",
    "liblockagent",
    "liblog.dylib",
    "liblog",
    "liblogwrap",
    "liblp",
    "liblpdump",
    "liblpdump_interface-cpp",
    "liblz4",
    "liblzma",
    "libm",
    "libmacaddr.dylib",
    "libmdnssd",
    "libmedia",
    "libmedia_codeclist",
    "libmedia_helper",
    "libmedia_jni",
    "libmedia_jni_utils",
    "libmedia_omx",
    "libmedia_omx_client",
    "libmediadrm",
    "libmediadrmmetrics_consumer",
    "libmediadrmmetrics_full",
    "libmediadrmmetrics_lite",
    "libmediaextractorservice",
    "libmedialogservice",
    "libmediametrics",
    "libmediametricsservice",
    "libmediandk",
    "libnl",
    "libmediandk_utils",
    "libmediaplayerservice",
    "libmediautils",
    "libmeminfo",
    "libmemtrack",
    "libmemtrackproxy",
    "libmemunreachable",
    "libminijail",
    "libminikin",
    "libminui",
    "libmtp",
    "libnativebridge_lazy",
    "libnativedisplay",
    "libnativeloader_lazy",
    "libnativewindow",
    "libnbaio",
    "libnblog",
    "libnetd_client",
    "libnetdbpf",
    "libnetdutils",
    "libnetlink",
    "libnetutils",
    "libneuralnetworks_packageinfo",
    "libnfc-nci",
    "libnfc_nci_jni",
    "libnum_integer.dylib",
    "libnum_traits.dylib",
    "libpackagelistparser",
    "libparameter",
    "libpcap",
    "libpcre2",
    "libpdfium",
    "libpdx_default_transport",
    "libperfetto",
    "libperfetto_android_internal",
    "libpermission",
    "libpiex",
    "libpng",
    "libpolicy-subsystem",
    "libpower",
    "libpowermanager",
    "libppv_lite86.dylib",
    "libprintspooler_jni",
    "libprocessgroup",
    "libprocessgroup_setup",
    "libprocinfo",
    "libprofcollectd_aidl_interface.dylib",
    "libprotobuf-cpp-full",
    "libprotobuf-cpp-lite",
    "libprotoutil",
    "libpsi",
    "libpuresoftkeymasterdevice",
    "libqtaguid",
    "libradio_metadata",
    "librand.dylib",
    "librand_chacha.dylib",
    "librand_core.dylib",
    "libremote-processor",
    "libresourcemanagerservice",
    "librs_jni",
    "librtp_jni",
    "libryu.dylib",
    "libschedulerservicehidl",
    "libselinux",
    "libsensor",
    "libsensorprivacy",
    "libsensorservice",
    "libsensorservicehidl",
    "libserde.dylib",
    "libserde_json.dylib",
    "libservices",
    "libsfplugin_ccodec",
    "libsfplugin_ccodec_utils",
    "libshmemcompat",
    "libshmemutil",
    "libsimpleperf_profcollect",
    "libsoft_attestation_cert",
    "libsonic",
    "libsonivox",
    "libsoundpool",
    "libsparse",
    "libspeexresampler",
    "libsqlite",
    "libsquashfs_utils",
    "libssl",
    "libstagefright",
    "libstagefright_amrnb_common",
    "libstagefright_bufferpool@2.0.1",
    "libstagefright_bufferqueue_helper",
    "libstagefright_codecbase",
    "libstagefright_foundation",
    "libstagefright_framecapture_utils",
    "libstagefright_http_support",
    "libstagefright_httplive",
    "libstagefright_omx",
    "libstagefright_omx_utils",
    "libstagefright_xmlparser",
    "libstatshidl",
    "libstatslog",
    "libstd.dylib",
    "libstdc++",
    "libsync",
    "libsysutils",
    "libthiserror.dylib",
    "libtimeinstate",
    "libtimestats",
    "libtimestats_atoms_proto",
    "libtimestats_proto",
    "libtinyalsa",
    "libtinyxml2",
    "libtombstoned_client",
    "libtracingproxy",
    "libui",
    "libuinputcommand_jni",
    "libunwindstack",
    "libupdate_engine_stable-V1-cpp",
    "libusbhost",
    "libutils",
    "libutilscallstack",
    "libuuid.dylib",
    "libvibrator",
    "libvibratorservice",
    "libvintf",
    "libvkjson",
    "libvndksupport",
    "libvulkan",
    "libwebviewchromium_loader",
    "libwebviewchromium_plat_support",
    "libwfds",
    "libwifi-system-iface",
    "libwilhelm",
    "libxml2",
    "libyuv",
    "libz",
    "libzip.dylib",
    "libziparchive",
    "media_permission-aidl-cpp",
    "mediametricsservice-aidl-cpp",
    "netd_aidl_interface-V6-cpp",
    "netd_aidl_interface-V7-cpp",
    "netd_event_listener_interface-V1-cpp",
    "oemnetd_aidl_interface-cpp",
    "pppol2tp-android",
    "pppopptp-android",
    "server_configurable_flags",
    "service.incremental",
    "shared-file-region-aidl-cpp",
    "slicer",
    "spatializer-aidl-cpp",
    "libcups",
    "libwfds",
    "libnfc_nci_jni",
    "libprintspooler_jni",
    "libbluetooth_jni",
    "libemulator_multidisplay_jni",
    "libemulator_multidisplay_jni",
    "libGLESv1_CM_angle",
    "libGLESv2_angle",
    "libGLESv1_CM_emulation",
    "libGLESv2_emulation",
    "libEGL_angle",
    "libEGL_emulation",
    "gralloc.default",
    "android.hardware.graphics.mapper@3.0-impl-ranchu",
    "vulkan.ranchu",
    "libGLESv1_enc",
    "libGLESv2_enc",
    "libGoldfishProfiler",
    "libOpenglCodecCommon",
    "libOpenglSystemCommon",
    "lib_renderControl_enc",
    "libandroidemu",
    "libdrm",
    "libvulkan_enc",
    "libjni_latinime",
    "libframesequence",
    "libjni_jpegutil",
    "libjni_jpegstream",
    "libjni_filtershow_filters",
    "libjni_eglfence",
    "libjni_tinyplanet",
    "libgiftranscode",
    "libjni_jpegutil",
    "libjni_tinyplanet",
    "libjni_jpegstream",
    "libjni_filtershow_filters",
    "libjni_eglfence",
    "libjni_latinime",
    "libadb_protos",
    "libclang_rt.scudo_minimal-aarch64-android",
    "libclang_rt.scudo_minimal-arm-android",
    "libclang_rt.scudo-aarch64-android",
    "libclang_rt.scudo-arm-android",
    "libclang_rt.ubsan_standalone-arm-android",
    "libclang_rt.asan-arm-android",
    "libstatssocket",
    "android.hardware.gnss-V1-ndk_platform",
    "android.hardware.power-V2-ndk_platform",
    "lib_profiler",
    "libprofiler_support",
    "libprofiler",
]

APEX_NATIVE_LIBS = [
    "libnetd_resolv",
    "libneuralnetworks",        # Apex: com.android.neuralnetworks
    "libadb_pairing_server",    # Apex: com.android.adbd
    "libc_malloc_hooks",        # Apex: com.android.runtime
    "libc_malloc_debug",        # Apex: com.android.runtime
    "libperfetto_hprof",        # Apex: com.android.art and com.android.art.debug
    "libcodec2_hidl@1.2"        # Apex: com.android.media.swcodec
    "libstatspull"              # Apex: com.android.os.statsd
    "libstats_jni"              # Apex: com.android.os.statsd

]