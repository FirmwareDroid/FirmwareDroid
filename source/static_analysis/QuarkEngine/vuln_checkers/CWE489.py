from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE489(VulnCheck):

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path

    def verify(self):
        from quark.script import getApplication
        result = None
        if getApplication(self.apk_path).isDebuggable():
            finding = "Active Debug Code is detected. The application is debuggable."
            result = {"CWE489": finding}

        return result
