import os
from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE22(VulnCheck):
    string_matching_api = [
        ["Ljava/lang/String;", "contains", "(Ljava/lang/CharSequence)Z"],
        ["Ljava/lang/String;", "indexOf", "(I)I"],
        ["Ljava/lang/String;", "indexOf", "(Ljava/lang/String;)I"],
        ["Ljava/lang/String;", "matches", "(Ljava/lang/String;)Z"],
    ]

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path
        self.rule_name = "accessFileInExternalDir.json"
        self.rule_path = os.path.abspath(os.path.join(rule_dir_path, self.rule_name))

    def verify(self):
        from quark.script import runQuarkAnalysis, Rule
        rule = Rule(self.rule_path)
        quark_result = runQuarkAnalysis(self.apk_path, rule)
        result_dict = None

        for accessExternalDir in quark_result.behaviorOccurList:
            argument_list = accessExternalDir.secondAPI.getArguments()
            if argument_list and len(argument_list) >= 3:
                filePath = argument_list[2]
                if quark_result.isHardcoded(filePath):
                    continue
                caller = accessExternalDir.methodCaller
                strMatchingAPIs = [
                    api
                    for api in self.string_matching_api
                    if quark_result.findMethodInCaller(caller, api)
                ]
                if not strMatchingAPIs:
                    result_dict = {"CWE22": f"Improper Limitation of a Pathname to a Restricted Directory "
                                            f"('Path Traversal') detected in method, {caller.fullName}"}

        return result_dict
