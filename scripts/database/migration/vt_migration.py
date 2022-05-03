"""
Script to migrate the virustotal collection from an old database to a newer
"""
import logging
import traceback
import flask
from model import VirusTotalReport, AndroidApp
from scripts.rq_tasks.flask_context_creator import create_app_context


def start_migration():
    """Copies VirusTotal entries from an old database to a new one."""
    create_app_context()
    db_con = connect_to_old_database()
    vt_report_list = get_vt_reports_from_old_db(db_con)
    add_app_references(vt_report_list)


def create_vt_report(report_datetime, file_info, analysis_id, virus_total_analysis):
    """
    Create a VirusTotalReport without saving it to the database.
    """
    if analysis_id:
        vt_report = VirusTotalReport(report_datetime=report_datetime,
                                     file_info=file_info)
    else:
        vt_report = VirusTotalReport(report_datetime=report_datetime,
                                     file_info=file_info,
                                     analysis_id=analysis_id,
                                     virus_total_analysis=virus_total_analysis)
    return vt_report


def add_app_references(vt_report_list):
    """
    Adds the android app reference to the VirusTotal report and saves the report to the database.

    :param vt_report_list: list(AndroidApp) - List of Class:AndroidApp objects.

    """
    for vt_report in vt_report_list:
        try:
            md5 = vt_report.file_info.data.attributes.md5
            android_app = find_app_reference(md5)
            vt_report.android_app_id_reference = android_app.pk
            vt_report.save()
        except Exception as err:
            logging.error(err)
            traceback.print_exc()


def find_app_reference(md5):
    """
    Finds an android app based on the md5 hash.

    :return: Class:AndroidApp

    """
    android_app = AndroidApp.objects.find(md5=md5).limit(1)
    return android_app


def get_vt_reports_from_old_db(db):
    """
    Fetches all the entries from the old database to a list of objects.

    :param db: pymongo db connection object.

    :return: list(Class:VirusTotalReport)
    """
    vt_collection = db["virus_total_report"]
    vt_report_list = []
    vt_data = vt_collection.find()
    for vt_entry in vt_data:
        report_datetime = vt_entry.report_datetime
        file_info = vt_entry.file_info
        if vt_entry.analysis_id:
            analysis_id = vt_entry.analysis_id
            virus_total_analysis = vt_entry.virus_total_analysis
            vt_report = create_vt_report(report_datetime,
                                         file_info,
                                         analysis_id,
                                         virus_total_analysis)
        else:
            vt_report = create_vt_report(report_datetime,
                                         file_info,
                                         analysis_id=None,
                                         virus_total_analysis=None)
        vt_report_list.append(vt_report)

    return vt_report_list


def connect_to_old_database():
    """
    Connects to the old database collection.

    :return: pymongo database connection

    """
    import pymongo
    from pymongo import MongoClient

    app = flask.current_app
    db_name = app.config["MONGODB_SETTINGS_OLD"].get("db")
    host = app.config["MONGODB_SETTINGS_OLD"].get("host")
    port = app.config["MONGODB_SETTINGS_OLD"].get("port")
    username = app.config["MONGODB_SETTINGS_OLD"].get("username")
    password = app.config["MONGODB_SETTINGS_OLD"].get("password")
    connection_string = f"mongodb+srv://{username}:{password}@{host}:{port}/{db_name}"
    client = MongoClient(connection_string)
    return client[db_name]
