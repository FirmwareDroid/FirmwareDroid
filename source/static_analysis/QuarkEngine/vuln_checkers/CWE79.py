import os
from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE79(VulnCheck):
    XSS_FILTERS = [
        [
            "Lorg/owasp/esapi/Validator;",
            "getValidSafeHTML",
            "(Ljava/lang/String; Ljava/lang/String; I Z)Ljava/lang/String;",
        ],
        [
            "Lorg/owasp/esapi/Encoder;",
            "encodeForHTML",
            "(Ljava/lang/String;)Ljava/lang/String;",
        ],
        [
            "Lorg/owasp/esapi/Encoder;",
            "encodeForJavaScript",
            "(Ljava/lang/String;)Ljava/lang/String;",
        ],
        [
            "Lorg/owasp/html/PolicyFactory;",
            "sanitize",
            "(Ljava/lang/String;)Ljava/lang/String;",
        ],
    ]

    target_method = ["Landroid/webkit/WebSettings;", "setJavaScriptEnabled", "(Z)V"]

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path
        self.rule_name = "loadUrlFromIntent2.json"
        self.rule_path = os.path.abspath(os.path.join(rule_dir_path, self.rule_name))
        if not os.path.exists(self.rule_path):
            raise FileNotFoundError(f"Rule file not found: {self.rule_path}")

    def verify(self):
        from quark.script import runQuarkAnalysis, Rule
        ruleInstance = Rule(self.rule_path)
        quarkResult = runQuarkAnalysis(self.apk_path, ruleInstance)

        result_list = []
        for loadUrl in quarkResult.behaviorOccurList:
            caller = loadUrl.methodCaller
            setJS = quarkResult.findMethodInCaller(caller, self.target_method)

            if setJS and len(setJS) > 0:
                argument_list = setJS[0].getArguments()
                if argument_list and len(argument_list) >= 2:
                    enableJS = argument_list[1]

                    if enableJS:
                        XSSFiltersInCaller = [
                            filterAPI
                            for filterAPI in self.XSS_FILTERS
                            if quarkResult.findMethodInCaller(caller, filterAPI)
                        ]

                        if not XSSFiltersInCaller:
                            finding = {"CWE79": f"Improper Neutralization of Input During Web Page Generation "
                                                f"(‘Cross-site Scripting’) in method, {caller.fullName}"}
                            result_list.append(finding)
        return {"CWE79": result_list}
