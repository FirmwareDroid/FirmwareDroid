import os
from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE94(VulnCheck):
    target_method = [
        "Landroid/content/pm/PackageManager;",
        "checkSignatures",
        "(Ljava/lang/String;Ljava/lang/String;)I"
    ]

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path
        self.rule_name = "loadExternalCode.json"
        self.rule_path = os.path.abspath(os.path.join(rule_dir_path, self.rule_name))
        if not os.path.exists(self.rule_path):
            raise FileNotFoundError(f"Rule file not found: {self.rule_path}")

    def verify(self):
        from quark.script import runQuarkAnalysis, Rule
        ruleInstance = Rule(self.rule_path)
        quarkResult = runQuarkAnalysis(self.apk_path, ruleInstance)

        result_list = []
        for ldExternalCode in quarkResult.behaviorOccurList:
            callerMethod = [
                ldExternalCode.methodCaller.className,
                ldExternalCode.methodCaller.methodName,
                ldExternalCode.methodCaller.descriptor
            ]
            if not quarkResult.findMethodInCaller(callerMethod, self.target_method):
                finding = {"CWE94": f"Improper Control of Generation of Code ('Code Injection') in {callerMethod}. "
                                    f"Method: {self.target_method[1]} not found!"}
                result_list.append(finding)

        return {"CWE94": result_list}
