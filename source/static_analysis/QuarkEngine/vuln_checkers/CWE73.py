import os
from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE73(VulnCheck):
    OPEN_FILE_API = [
        "Landroid/os/ParcelFileDescriptor;",  # Class name
        "open",  # Method name
        "(Ljava/io/File; I)Landroid/os/ParcelFileDescriptor;"  # Descriptor
    ]

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path
        self.rule_name = "accessFileInExternalDir.json"
        self.rule_path = os.path.abspath(os.path.join(rule_dir_path, self.rule_name))
        if not os.path.exists(self.rule_path):
            raise FileNotFoundError(f"Rule file not found: {self.rule_path}")

    def verify(self):
        from quark.script import runQuarkAnalysis, Rule
        ruleInstance = Rule(self.rule_path)
        quarkResult = runQuarkAnalysis(self.apk_path, ruleInstance)

        result_list = []
        for accessExternalDir in quarkResult.behaviorOccurList:
            filePath = accessExternalDir.secondAPI.getArguments()[2]
            if quarkResult.isHardcoded(filePath):
                continue
            caller = accessExternalDir.methodCaller
            result = quarkResult.findMethodInCaller(caller, self.OPEN_FILE_API)
            if result:
                result_list.append(f"External Control of File Name or Path is detected in method, {caller.fullName}")
        return {"CWE73": result_list}
