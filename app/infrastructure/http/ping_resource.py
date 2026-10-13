from http import HTTPStatus

from flask import current_app
from flask_restful import Resource

from app import constants


class PingResource(Resource):
    def get(self):
        return {constants.KEY_VERSION: current_app.config[constants.CONFIG_APP_VERSION]}, HTTPStatus.OK
