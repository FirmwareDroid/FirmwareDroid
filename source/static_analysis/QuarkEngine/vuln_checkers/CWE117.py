import os
from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE117(VulnCheck):
    KEYWORDS_FOR_NEUTRALIZATION = ["escape", "replace", "format", "setFilter"]

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path
        self.rule_name = "writeContentToLog.json"
        self.rule_path = os.path.abspath(os.path.join(rule_dir_path, self.rule_name))
        if not os.path.exists(self.rule_path):
            raise FileNotFoundError(f"Rule file not found: {self.rule_path}")

    def verify(self):
        from quark.script import runQuarkAnalysis, Rule
        ruleInstance = Rule(self.rule_path)
        quarkResult = runQuarkAnalysis(self.apk_path, ruleInstance)

        result_list = []
        for logOutputBehavior in quarkResult.behaviorOccurList:
            secondAPIParam = logOutputBehavior.getParamValues()[1]
            isKeywordFound = False
            for keyword in self.KEYWORDS_FOR_NEUTRALIZATION:
                if keyword in secondAPIParam:
                    isKeywordFound = True
                    break
            if not isKeywordFound:
                finding = {"CWE117": f"Improper Output Neutralization for Logs in method, {secondAPIParam}"}
                result_list.append(finding)

        return {"CWE117": result_list}
