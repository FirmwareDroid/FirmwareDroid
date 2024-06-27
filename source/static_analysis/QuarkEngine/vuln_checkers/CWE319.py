import os
from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE319(VulnCheck):
    protocol_keyword_list = [
        "http",
        "smtp",
        "ftp"
    ]

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path
        self.rule_name = "setRetrofitBaseUrl.json"
        self.rule_path = os.path.abspath(os.path.join(rule_dir_path, self.rule_name))
        if not os.path.exists(self.rule_path):
            raise FileNotFoundError(f"Rule file not found: {self.rule_path}")

    def verify(self):
        from quark.script import runQuarkAnalysis, Rule
        ruleInstance = Rule(self.rule_path)
        quarkResult = runQuarkAnalysis(self.apk_path, ruleInstance)

        result_list = []
        for setRetrofitBaseUrl in quarkResult.behaviorOccurList:
            for protocol in self.protocol_keyword_list:
                regexRule = f"{protocol}://[0-9A-Za-z./-]+"
                cleartextProtocolUrl = setRetrofitBaseUrl.hasString(regexRule, True)

                if cleartextProtocolUrl:
                    cleartext_urls = '\n'.join(cleartextProtocolUrl)
                    finding = {"CWE319": f"Cleartext Transmission of Sensitive Information protocol: {protocol} "
                                         f"in {setRetrofitBaseUrl.methodCaller.fullName};"
                                         f"URLs: {cleartext_urls}"}
                    result_list.append(finding)
        return {"CWE319": result_list}
