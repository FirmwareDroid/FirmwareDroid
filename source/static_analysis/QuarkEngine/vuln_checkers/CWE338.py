import os
from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE338(VulnCheck):
    credentials_keyword_list = [
        "token", "password", "account", "encrypt",
        "authentication", "authorization", "id", "key"
    ]

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path
        self.rule_name = "useMethodOfPRNG.json"
        self.rule_path = os.path.abspath(os.path.join(rule_dir_path, self.rule_name))
        if not os.path.exists(self.rule_path):
            raise FileNotFoundError(f"Rule file not found: {self.rule_path}")

    def verify(self):
        from quark.script import runQuarkAnalysis, Rule
        ruleInstance = Rule(self.rule_path)
        quarkResult = runQuarkAnalysis(self.apk_path, ruleInstance)

        result_list = []
        for usePRNGMethod in quarkResult.behaviorOccurList:
            for prngCaller in usePRNGMethod.methodCaller.getXrefFrom():
                if any(keyword in prngCaller.fullName for keyword in self.credentials_keyword_list):
                    finding = {"CWE338": f"Use of Cryptographically Weak Pseudo-Random Number Generator (PRNG)"
                                         f" is detected in {prngCaller.fullName}"}
                    result_list.append(finding)
        return {"CWE338": result_list}
