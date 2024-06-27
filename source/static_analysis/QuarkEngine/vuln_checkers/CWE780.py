import os
from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE780(VulnCheck):

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path
        self.rule_name = "useOfCryptographicAlgo.json"
        self.rule_path = os.path.abspath(os.path.join(rule_dir_path, self.rule_name))

    def verify(self):
        from quark.script import runQuarkAnalysis, Rule
        rule = Rule(self.rule_path)
        quark_result = runQuarkAnalysis(self.apk_path, rule)
        result = None

        for useCryptographicAlgo in quark_result.behaviorOccurList:
            methodCaller = useCryptographicAlgo.methodCaller

            if useCryptographicAlgo.hasString("RSA") and not useCryptographicAlgo.hasString("OAEP"):
                result = {"CWE780": f"Use of RSA Algorithm without OAEP is detected in method, {methodCaller.fullName}"}

        return result
