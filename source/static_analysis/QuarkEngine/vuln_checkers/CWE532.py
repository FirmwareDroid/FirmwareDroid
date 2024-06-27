import os
from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE532(VulnCheck):
    target_method_list = [
        "Landroid/util/Log;",  # class name
        "d",  # method name
        "(Ljava/lang/String; Ljava/lang/String;)I"  # descriptor
    ]
    credential_keywords = [
        "token",
        "decrypt",
        "password"
    ]

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path
        self.rule_name = "deserializeData.json"
        self.rule_path = os.path.abspath(os.path.join(rule_dir_path, self.rule_name))
        if not os.path.exists(self.rule_path):
            raise FileNotFoundError(f"Rule file not found: {self.rule_path}")

    def verify(self):
        from quark.script import findMethodInAPK
        result_list = []

        methodsFound = findMethodInAPK(self.apk_path, self.target_method_list)
        for debugLogger in methodsFound:
            arguments = debugLogger.getArguments()

            for keyword in self.credential_keywords:
                if len(arguments) >= 2 and keyword in arguments[1]:
                    result_list.append(f"Insertion of Sensitive Information into Log File"
                                       f" is detected in method, {debugLogger.fullName}")

        return {"CWE532": result_list}
