from http import HTTPStatus

from flask_jwt_extended import JWTManager

from app import constants


def register_jwt_error_handlers(jwt_manager: JWTManager) -> None:
    @jwt_manager.unauthorized_loader
    def handle_missing_token(reason: str):
        return {constants.KEY_MSG: constants.MESSAGE_MISSING_TOKEN}, HTTPStatus.UNAUTHORIZED

    @jwt_manager.invalid_token_loader
    def handle_invalid_token(reason: str):
        return {constants.KEY_MSG: constants.MESSAGE_INVALID_TOKEN}, HTTPStatus.UNAUTHORIZED
