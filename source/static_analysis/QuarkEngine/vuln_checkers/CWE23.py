import os
from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE23(VulnCheck):
    STRING_MATCHING_API = [
        ["Ljava/lang/String;", "contains", "(Ljava/lang/CharSequence)Z"],
        ["Ljava/lang/String;", "indexOf", "(I)I"],
        ["Ljava/lang/String;", "indexOf", "(Ljava/lang/String;)I"],
        ["Ljava/lang/String;", "matches", "(Ljava/lang/String;)Z"],
        [
            "Ljava/lang/String;",
            "replaceAll",
            "(Ljava/lang/String; Ljava/lang/String;)Ljava/lang/String;",
        ],
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
            argument_list = accessExternalDir.secondAPI.getArguments()
            if argument_list and len(argument_list) >= 3:
                filePath = argument_list[2]
                if quarkResult.isHardcoded(filePath):
                    continue
                caller = accessExternalDir.methodCaller
                strMatchingAPIs = [
                    api
                    for api in self.STRING_MATCHING_API
                    if quarkResult.findMethodInCaller(caller, api)
                ]
                if not strMatchingAPIs or ".." not in strMatchingAPIs:
                    result_list.append(f"Relative Path Traversal detected in method, {caller.fullName}")

        return {"CWE23": result_list}
