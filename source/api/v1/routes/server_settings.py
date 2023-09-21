# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
# import flask
# from flask_restx import Resource, Namespace

from model.StoreSetting import FILE_STORE_NAME_LIST
from config.app_settings import set_active_storage_folders
from api.v1.decorators.jwt_auth_decorator import admin_jwt_required
from model import ApplicationSetting, StoreSetting
from model.ApplicationSetting import ApplicationSettingSchema
ns = Namespace('server_settings', description='Operations related to application settings.')


@ns.route('/client_setting/')
class GetApplicationSetting(Resource):
    def get(self):
        """
        Get application settings for a client.

        :return: json - public configuration data for clients.

        """
        response = "", 400
        app_setting = ApplicationSetting.objects.first()
        if app_setting:
            response = ApplicationSettingSchema().dump(app_setting)
        return response


@ns.route('/file_store_setting/<string:file_store_name>')

class SetActiveStorage(Resource):
    @admin_jwt_required
    def post(self, file_store_name):
        """
        Sets the active file storage of the application. Important: After updating this option the server needs to be
        immediately restarted (manually). Otherwise only one web worker will have an updated setting and the others
        will keep the old settings.

        :param file_store_name: str - name of the file store to use

        """
        response = "", 400
        store_setting = StoreSetting.objects.first()
        if store_setting:
            if file_store_name in FILE_STORE_NAME_LIST:
                store_setting.active_store_name = file_store_name
                store_setting.save()
                app_instance = flask.current_app
                set_active_storage_folders(app_instance)
                response = "", 200
            else:
                logging.error("Invalid file storage name.")
        else:
            logging.error("No store setting in database!")
        return response
