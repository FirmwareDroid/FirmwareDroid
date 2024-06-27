import os
from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE749(VulnCheck):
    target_method = [
        "Landroid/webkit/WebView;",
        "addJavascriptInterface",
        "(Ljava/lang/Object; Ljava/lang/String;)V"
    ]

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path
        self.rule_name = "configureJsExecution.json"
        self.rule_path = os.path.abspath(os.path.join(rule_dir_path, self.rule_name))

    def verify(self):
        from quark.script import runQuarkAnalysis, Rule
        rule = Rule(self.rule_path)
        quark_result = runQuarkAnalysis(self.apk_path, rule)
        result_list = []

        for configureJsExecution in quark_result.behaviorOccurList:
            caller = configureJsExecution.methodCaller
            secondAPI = configureJsExecution.secondAPI
            enableJS = secondAPI.getArguments()[1]
            exposeAPI = quark_result.findMethodInCaller(caller, self.target_method)

            if enableJS and exposeAPI:
                finding = (f"Exposed Dangerous Method or Function"
                           f" is detected in method, {caller.fullName}")
                result_list.append(finding)

        return {"CWE749": result_list}
