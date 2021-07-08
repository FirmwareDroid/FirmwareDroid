# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
from flask_restx import Resource, Namespace
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from scripts.auth.basic_auth import requires_basic_authorization
from scripts.dynamic_analysis.emulator_control.emulator_runner import start_frida_server_installation, \
    start_frida_smoke_test
from model.FridaScript import FridaScript

ns = Namespace('frida', description='Operations related to Frida dynamic instrumentation.')

parser = ns.parser()
parser.add_argument('file', type=FileStorage, location='files')


@ns.route('/upload_script/')
class AddFridaScript(Resource):
    @ns.doc('post')
    @ns.expect(parser)
    @requires_basic_authorization
    def post(self):
        response = "", 200
        try:
            args = parser.parse_args()
            file = args.get('file')
            file.save(secure_filename(file.filename))
            logging.info(file.filename)
            FridaScript(script_name=file.filename, code_file=file).save()
        except Exception as err:
            logging.error(err)
            response = "", 400
        return response


@ns.route('/install_server/')
class InstallFridaServer(Resource):
    @ns.doc('post')
    @requires_basic_authorization
    def post(self):
        response = "", 200
        try:
            emulator_url = "firmware-emulator.cloudlab.zhaw.ch"
            emulator_port = 5555
            frida_port = 27042
            start_frida_server_installation(emulator_url, emulator_port, frida_port)
        except Exception as err:
            logging.error(err)
            response = "", 400
        return response


@ns.route('/run_frida_smoke_test/<string:device_ip>/<string:frida_port>')
class RunFridaSmoke(Resource):
    @ns.doc('post')
    @requires_basic_authorization
    def post(self, device_ip, frida_port):
        response = "", 200
        try:
            #emulator_url = "firmware-emulator.cloudlab.zhaw.ch"
            #frida_port = 27042
            start_frida_smoke_test(device_ip, frida_port)
        except Exception as err:
            logging.error(err)
            response = "", 400
        return response
