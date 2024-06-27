from static_analysis.QuarkEngine.VulnCheck import VulnCheck


class CWE926(VulnCheck):
    def __init__(self, apk_path, rule_dir_path):
        self.apk_path = apk_path
        self.rule_name = None
        self.rule_path = None

    def verify(self):
        from quark.script import getActivities
        result_list = []

        for activityInstance in getActivities(self.apk_path):
            if activityInstance.hasIntentFilter() and activityInstance.isExported():
                finding = (f"Improper Export of Android Application Components"
                           f" is detected in the activity, {activityInstance}")
                result_list.append(finding)

        return {"CWE926": result_list}
