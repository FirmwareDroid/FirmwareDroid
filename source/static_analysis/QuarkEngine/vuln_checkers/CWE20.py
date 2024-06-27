import logging
import os.path
from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE20(VulnCheck):
    validate_methods = ["contains", "indexOf", "matches", "replaceAll"]

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path
        self.rule_name = "openUrlThatUserInput.json"
        self.rule_path = os.path.abspath(os.path.join(rule_dir_path, self.rule_name))
        if not os.path.exists(self.rule_path):
            raise FileNotFoundError(f"Rule file not found: {self.rule_path}")

    def verify(self):
        logging.debug(f"Rule name: {self.rule_name} {self.apk_path}, {self.rule_path}")
        from quark.script import runQuarkAnalysis, Rule
        if not self.rule_name or not self.rule_path:
            raise FileNotFoundError(f"Rule name and path not set: {self.rule_name}, {self.rule_path}")
        rule = Rule(self.rule_path)
        quark_result = runQuarkAnalysis(self.apk_path, rule)
        result = None

        for openUrl in quark_result.behaviorOccurList:
            calledMethods = openUrl.getMethodsInArgs()
            if not any(method.methodName in self.validate_methods for method in calledMethods):
                result = {"CWE20": f"Improper Input Validation detected in method, {openUrl.methodCaller.fullName}"}

        return result
