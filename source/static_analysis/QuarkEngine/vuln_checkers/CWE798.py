import re
import os
from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE798(VulnCheck):

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path
        self.rule_name = "findSecretKeySpec.json"
        self.rule_path = os.path.abspath(os.path.join(rule_dir_path, self.rule_name))
        if not os.path.exists(self.rule_path):
            raise FileNotFoundError(f"Rule file not found: {self.rule_path}")

    def verify(self):
        from quark.script import runQuarkAnalysis, Rule
        rule = Rule(self.rule_path)
        quark_result = runQuarkAnalysis(self.apk_path, rule)
        result_list = []

        for secretKeySpec in quark_result.behaviorOccurList:
            param_value_list = secretKeySpec.getParamValues()
            if param_value_list and len(param_value_list) >= 2:
                firstParam = param_value_list[1]
                secondParam = param_value_list[2]
                if secondParam == "AES":
                    AESKey = re.findall(r"\((.*?)\)", firstParam)[1]
                    if quark_result.isHardcoded(AESKey):
                        finding = {"CWE798": f"Use of Hard-coded Credentials found {secondParam} key {AESKey}"}
                        result_list.append(finding)
        return {"CWE798": result_list}
