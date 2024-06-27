from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE295(VulnCheck):
    target_method_list = [
        "Landroid/webkit/SslErrorHandler;",  # class name
        "proceed",  # method name
        "()V"  # descriptor
    ]
    override_method_list = [
        "Landroid/webkit/WebViewClient;",  # class name
        "onReceivedSslError",  # method name
        "(Landroid/webkit/WebView;" + " Landroid/webkit/SslErrorHandler;" + \
        " Landroid/net/http/SslError;)V"  # descriptor
    ]

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path

    def verify(self):
        from quark.script import findMethodInAPK
        result_list = []
        for sslProceedCaller in findMethodInAPK(self.apk_path, self.target_method_list):
            if (sslProceedCaller.name == self.override_method_list[1] and
                    sslProceedCaller.descriptor == self.override_method_list[2] and
                    self.override_method_list[0] in sslProceedCaller.findSuperclassHierarchy()):
                result_list.append(f"Improper Certificate Validation is detected in method, "
                                   f"{sslProceedCaller.fullName}")
        return {"CWE295": result_list}
