import os
from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE940(VulnCheck):
    intent_settings_method_list = [
        "findViewById",
        "getStringExtra",
        "getIntent",
    ]

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path
        self.rule_name = "loadUrlFromIntent.json"
        self.rule_path = os.path.abspath(os.path.join(rule_dir_path, self.rule_name))
        if not os.path.exists(self.rule_path):
            raise FileNotFoundError(f"Rule file not found: {self.rule_path}")

    def verify(self):
        from quark.script import runQuarkAnalysis, Rule
        ruleInstance = Rule(self.rule_path)
        quarkResult = runQuarkAnalysis(self.apk_path, ruleInstance)
        result_list = []

        for behaviorInstance in quarkResult.behaviorOccurList:
            methodsInArgs = behaviorInstance.getMethodsInArgs()

            verifiedMethodCandidates = []
            for method in methodsInArgs:
                if method.methodName not in self.intent_settings_method_list:
                    verifiedMethodCandidates.append(method)
            if len(verifiedMethodCandidates) == 0:
                caller = behaviorInstance.methodCaller.fullName
                finding = {"CWE940": f"Improper Verification of Source of a Communication Channel"
                                     f" is detected in method, {caller}"}
                result_list.append(finding)

        return {"CWE940": result_list}
