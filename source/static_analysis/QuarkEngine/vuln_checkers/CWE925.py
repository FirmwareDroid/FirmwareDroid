from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE925(VulnCheck):
    target_method_list = [
        '',
        'onReceive',
        '(Landroid/content/Context; Landroid/content/Intent;)V'
    ]

    check_method_list = [
        ['Landroid/content/Intent;', 'getAction', '()Ljava/lang/String;']
    ]

    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path
        self.rule_name = None
        self.rule_path = None

    def verify(self):
        from quark.script import checkMethodCalls, getReceivers
        result_list = []

        receivers = getReceivers(self.apk_path)
        for receiver in receivers:
            if receiver.isExported():
                className = "L" + str(receiver).replace('.', '/') + ';'
                self.target_method_list[0] = className
                if not checkMethodCalls(self.apk_path, self.target_method_list, self.check_method_list):
                    finding = (f"Improper Verification of Intent by Broadcast Receiver is "
                               f"detected in method, {className}")
                    result_list.append(finding)

        return {"CWE925": result_list}
