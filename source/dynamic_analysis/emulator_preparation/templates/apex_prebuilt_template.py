APEX_PREBUILT_TEMPLATE = "prebuilt_apex {\n" \
                         "name: \"${apex_name}\",\n" \
                         "overrides: [],\n" \
                         "arch: {\n" \
                         "arm64: {src: \"${apex_relative_path_arm64}\",},\n" \
                         "x86_64: {src: \"${apex_relative_path_x86_x64}\",},\n" \
                         "},\n" \
                         "filename: \"${apex_filename}\",\n" \
                         "prefer: true,\n" \
                         "installable: true\n" \
                         "}"

APEX_TEMPLATE = "apex {\n" \
                "name: \"${apex_name}\",\n" \
                "manifest: \"$apex_manifest.json\",\n" \
                "file_contexts: \"$file_contexts\",\n" \
                "${native_shared_libs}" \
                "${binaries}" \
                "${java_libs}" \
                "prebuilts: [],\n" \
                "compile_multilib: \"both\",\n" \
                "key: \"${apex_name}.key\",\n" \
                "certificate: \"${certificate}\",\n" \
                "}"

APEX_MANIFEST_TEMPLATE = "{\n" \
                            "  \"version\": ${apex_version},\n" \
                            "  \"name\": \"${apex_name}\",\n" \
                            "}"


APEX_EMULATOR_LIST = [".android.tethering.apex",
                      ".android.i18n.apex",
                      ".android.extservices.apex",
                      ".android.conscrypt.apex",
                      ".android.wifi.apex",
                      ".android.cellbroadcast.apex",
                      ".android.mediaprovider.apex",
                      ".android.sdkext.apex",
                      ".android.ipsec.apex",
                      ".android.resolv.apex",
                      ".android.os.statsd.apex",
                      ".android.runtime.apex",
                      ".android.art.apex",  
                      ".android.media.swcodec.apex",
                      ".android.scheduling.apex",
                      ".android.appsearch.apex",
                      ".android.neuralnetworks.apex",
                      ".android.media.apex",
                      ".android.permission.apex",
                      ".android.tethering.capex",
                      ".android.i18n.capex",
                      ".android.extservices.capex",
                      ".android.conscrypt.capex",
                      ".android.wifi.capex",
                      ".android.cellbroadcast.capex",
                      ".android.mediaprovider.capex",
                      ".android.sdkext.capex",
                      ".android.ipsec.capex",
                      ".android.resolv.capex",
                      ".android.os.statsd.capex",
                      ".android.runtime.capex",
                      ".android.art.capex",
                      ".android.media.swcodec.capex",
                      ".android.scheduling.capex",
                      ".android.appsearch.capex",
                      ".android.neuralnetworks.capex",
                      ".android.media.capex",
                      ".android.permission.capex"
                      ]
