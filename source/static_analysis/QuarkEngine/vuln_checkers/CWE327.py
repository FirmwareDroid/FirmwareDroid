import os
from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE327(VulnCheck):
    weak_algorithm_list = ["DES", "ARC4", "BLOWFISH"]

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path
        self.rule_name = "useOfCryptographicAlgo.json"
        self.rule_path = os.path.abspath(os.path.join(rule_dir_path, self.rule_name))
        if not os.path.exists(self.rule_path):
            raise FileNotFoundError(f"Rule file not found: {self.rule_path}")

    def verify(self):
        from quark.script import runQuarkAnalysis, Rule
        ruleInstance = Rule(self.rule_path)
        quarkResult = runQuarkAnalysis(self.apk_path, ruleInstance)
        result_list = []
        for useCryptoAlgo in quarkResult.behaviorOccurList:
            caller = useCryptoAlgo.methodCaller
            for algo in self.weak_algorithm_list:
                if useCryptoAlgo.hasString(algo):
                    finding = {"CWE327": f"Use of a Broken or Risky Cryptographic Algorithm"
                                         f" is detected {algo} in method, {caller.fullName}"}
                    result_list.append(finding)

        return {"CWE327": result_list}
