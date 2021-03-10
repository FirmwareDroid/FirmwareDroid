from scripts.database.query_document import get_filtered_list
from model import ExodusReport, AndroidApp
from scripts.rq_tasks.flask_context_creator import create_app_context


def start_exodus_scan(android_app_id_list):
    """
    Analysis all apps from the given list with exodus-core.
    :param android_app_id_list: list of class:'AndroidApp' object-ids.
    """
    create_app_context()
    android_app_list = get_filtered_list(android_app_id_list, AndroidApp, "exodus_report_reference")
    for android_app in android_app_list:
        exodus_json_report = exodus_analysis(android_app.absolute_path)
        create_report(android_app.id, exodus_json_report)


def exodus_analysis(apk_file_path):
    """
    Analyses one apk with exodus and creates a json report.
    :param apk_file_path: str - path to the apk file.
    :return: dict - exodus results as json.
    """
    from exodus_core.analysis.static_analysis import StaticAnalysis

    class AnalysisHelper(StaticAnalysis):
        def create_json_report(self):
            return {
                'application': {
                    'handle': self.get_package(),
                    'version_name': self.get_version(),
                    'version_code': self.get_version_code(),
                    'uaid': self.get_application_universal_id(),
                    'name': self.get_app_name(),
                    'permissions': self.get_permissions(),
                    'libraries': [l for l in self.get_libraries()],
                },
                'apk': {
                    'path': self.apk_path,
                    'checksum': self.get_sha256(),
                },
                'trackers': [
                    {'name': t.name, 'id': t.id} for t in self.detect_trackers()
                ],
            }

    analysis = AnalysisHelper(apk_file_path)
    analysis.load_trackers_signatures()
    return analysis.create_json_report()


def create_report(android_app, exodus_results):
    """
    Create a exodus report in the database.
    :param android_app: class:'AndroidApp'
    :param exodus_results: dict - results of the exodus scan.
    :return:
    """
    from exodus_core import __version__
    exodus_report = ExodusReport(
        android_app_id_reference=android_app.id,
        version=__version__,
        results=exodus_results
    ).save()
    android_app.exodus_report_reference = exodus_report.id
    android_app.save()
