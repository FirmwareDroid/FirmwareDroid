from flask_restx import Resource, Namespace
from scripts.auth.basic_auth import requires_basic_authorization

ns = Namespace('settings', description='Operations related to application settings.')


@ns.route('/change_settings/')
class SetSetting(Resource):
    def post(self):
        """
        Change the default application settings.
        :return:
        """
        # TODO Implement application settings
        return 200


@ns.route('/set_basic_auth/')
class SetSetting(Resource):
    @requires_basic_authorization
    def post(self):
        """
        De-/Activate basic authentication.
        :return:
        """
        # TODO Implement application settings
        return 200



























