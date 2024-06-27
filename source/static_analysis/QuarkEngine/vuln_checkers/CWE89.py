import os
from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE89(VulnCheck):
    target_method = [
        "Landroid/widget/EditText;",  # class name
        "getText",  # method name
        "()Landroid/text/Editable;",  # descriptor
    ]

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path
        self.rule_name = "executeSQLCommand.json"
        self.rule_path = os.path.abspath(os.path.join(rule_dir_path, self.rule_name))
        if not os.path.exists(self.rule_path):
            raise FileNotFoundError(f"Rule file not found: {self.rule_path}")

    def verify(self):
        from quark.script import runQuarkAnalysis, Rule
        ruleInstance = Rule(self.rule_path)
        quarkResult = runQuarkAnalysis(self.apk_path, ruleInstance)

        result_list = []
        for sqlCommandExecution in quarkResult.behaviorOccurList:
            if sqlCommandExecution.isArgFromMethod(self.target_method):
                finding = {"CWE89": f"Improper Neutralization of Special Elements used in an SQL "
                                    f"Command ('SQL Injection') detected in {sqlCommandExecution.methodCaller.fullName}"}
                result_list.append(finding)
        return {"CWE89": result_list}
