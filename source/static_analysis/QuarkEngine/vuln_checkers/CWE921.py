import os
from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE921(VulnCheck):
    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path
        self.rule_name = "checkFileExistence.json"
        self.rule_path = os.path.abspath(os.path.join(rule_dir_path, self.rule_name))
        if not os.path.exists(self.rule_path):
            raise FileNotFoundError(f"Rule file not found: {self.rule_path}")

    def verify(self):
        from quark.script import runQuarkAnalysis, Rule
        rule = Rule(self.rule_path)
        quark_result = runQuarkAnalysis(self.apk_path, rule)
        result_list = []

        for existingFile in quark_result.behaviorOccurList:
            filePath = existingFile.getParamValues()[0]
            if "sdcard" in filePath:
                finding = {"CWE921": f"Storage of Sensitive Data in a Mechanism without Access Control."
                                     f"File is stored inside the SDcard {filePath} and can be accessed "
                                     f"by other apps"}
                result_list.append(finding)

        return {"CWE921": result_list}
