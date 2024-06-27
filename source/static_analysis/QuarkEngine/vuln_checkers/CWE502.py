import os
from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE502(VulnCheck):
    verification_api_list = [
        ["Ljava/io/File;", "exists", "()Z"],
        ["Landroid/content/Context;", "getFilesDir", "()Ljava/io/File;"],
        ["Landroid/content/Context;", "getExternalFilesDir", "(Ljava/lang/String;)Ljava/io/File;"],
        ["Landroid/os/Environment;", "getExternalStorageDirectory", "()Ljava/io/File;"],
    ]

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path
        self.rule_name = "deserializeData.json"
        self.rule_path = os.path.abspath(os.path.join(rule_dir_path, self.rule_name))
        if not os.path.exists(self.rule_path):
            raise FileNotFoundError(f"Rule file not found: {self.rule_path}")

    def verify(self):
        from quark.script import runQuarkAnalysis, Rule
        rule = Rule(self.rule_path)
        quark_result = runQuarkAnalysis(self.apk_path, rule)
        result = None

        for dataDeserialization in quark_result.behaviorOccurList:
            apis = dataDeserialization.getMethodsInArgs()
            caller = dataDeserialization.methodCaller
            if not any(api in apis for api in self.verification_api_list):
                result = {"CWE502": f"Deserialization of Untrusted Data is detected in method, {caller.fullName}"}

        return result
