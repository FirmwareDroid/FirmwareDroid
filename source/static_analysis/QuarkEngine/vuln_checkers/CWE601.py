from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE601(VulnCheck):
    target_method_list = ["", "startActivity", "(Landroid/content/Intent;)V"]
    external_input_methods = [
        "getIntent",
        "getQueryParameter"
    ]
    input_filter_methods = [
        "parse",
        "isValidUrl",
        "Pattern",
        "Matcher",
        "encode",
        "decode",
        "escapeHtml",
        "HttpURLConnection"
    ]

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path

    def verify(self):
        from quark.script import findMethodInAPK
        redirect_method_list = findMethodInAPK(self.apk_path, self.target_method_list)

        result_list = []
        if redirect_method_list is not None:
            for redirectMethod in redirect_method_list:
                argument_list = redirectMethod.getArguments()
                if argument_list is not None:
                    for argument in argument_list:
                        if any(externalInput in argument for
                               externalInput in self.external_input_methods):
                            if not any(filterMethod in argument for
                                       filterMethod in self.input_filter_methods):
                                result_list.append(f"URL Redirection to Untrusted Site ('Open Redirect')File"
                                                   f" is detected in {redirectMethod.fullName}")
        if len(result_list) == 0:
            result = None
        else:
            result = {"CWE601": result_list}

        return result
