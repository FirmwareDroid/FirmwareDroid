import os
from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE78(VulnCheck):
    STRING_MATCHING_API = {("Ljava/lang/String;", "contains", "(Ljava/lang/CharSequence)Z"),
                           ("Ljava/lang/String;", "indexOf", "(I)I"),
                           ("Ljava/lang/String;", "indexOf", "(Ljava/lang/String;)I"),
                           ("Ljava/lang/String;", "matches", "(Ljava/lang/String;)Z"), (
                           "Ljava/lang/String;", "replaceAll",
                           "(Ljava/lang/String; Ljava/lang/String;)Ljava/lang/String;")}

    special_elements_pattern = r"[ ;|,>`]+"

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path
        self.rule_name = "externalStringCommand.json"
        self.rule_path = os.path.abspath(os.path.join(rule_dir_path, self.rule_name))
        if not os.path.exists(self.rule_path):
            raise FileNotFoundError(f"Rule file not found: {self.rule_path}")

    def verify(self):
        from quark.script import runQuarkAnalysis, Rule, findMethodInAPK
        ruleInstance = Rule(self.rule_path)
        quarkResult = runQuarkAnalysis(self.apk_path, ruleInstance)

        result_list = []
        for ExternalStringCommand in quarkResult.behaviorOccurList:
            methodCalled = set()
            caller = ExternalStringCommand.methodCaller
            for method in ExternalStringCommand.getMethodsInArgs():
                methodCalled.add(method.fullName)
            if methodCalled.intersection(self.STRING_MATCHING_API) and not ExternalStringCommand.hasString(
                    self.special_elements_pattern):
                continue
            else:
                finding = {"CWE78": f"Improper Neutralization of Special Elements used in an "
                                    f"OS Command detected in method, {caller.fullName}"}
                result_list.append(finding)
        return {"CWE78": result_list}
