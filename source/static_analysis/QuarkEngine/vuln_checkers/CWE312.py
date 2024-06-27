from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE312(VulnCheck):
    target_method = "android.app." \
                    "SharedPreferencesImpl$EditorImpl." \
                    "putString"

    target_param_type = "java.lang.String," \
                        "java.lang.String"

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path

    def verify(self):
        from quark.script.frida import runFridaHook
        from quark.script.ciphey import checkClearText

        fridaResult = runFridaHook(self.apk_path,
                                   self.target_method,
                                   self.target_param_type,
                                   secondToWait=10)
        result_list = []
        for putString in fridaResult.behaviorOccurList:
            firstParam, secondParam = putString.getParamValues()
            if firstParam in ["email", "password"] and \
                    secondParam == checkClearText(secondParam):
                result_list.append(f'Cleartext Storage of Sensitive Information. The cleartext is "{secondParam} '
                                   f'for the key "{firstParam}"')

        return {"CWE312": result_list}
