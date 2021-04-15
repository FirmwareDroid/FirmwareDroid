from flask_restx import Resource, Namespace
from model import ApplicationSetting
from model.ApplicationSetting import ApplicationSettingSchema
ns = Namespace('client_settings', description='Operations related to application settings.')


@ns.route('/change_settings/')
class SetSetting(Resource):
    def post(self):
        """
        Change the default application settings.
        :return:
        """
        # TODO Implement application settings
        return "Not implemented", 400


@ns.route('/client_setting/')
class GetClientSetting(Resource):
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
