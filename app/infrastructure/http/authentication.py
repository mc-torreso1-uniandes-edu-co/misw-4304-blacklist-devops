import hmac
from functools import wraps
from http import HTTPStatus
from typing import Optional

from flask import current_app, request

from app import constants


def extract_bearer_token(authorization_header: Optional[str]) -> Optional[str]:
    if not authorization_header or not authorization_header.startswith(constants.BEARER_PREFIX):
        return None
    return authorization_header[len(constants.BEARER_PREFIX):]


def is_valid_bearer_token(authorization_header: Optional[str], expected_token: Optional[str]) -> bool:
    received_token = extract_bearer_token(authorization_header)
    if received_token is None or not expected_token:
        return False
    return hmac.compare_digest(received_token.encode(), expected_token.encode())


def require_bearer_token(view):
    @wraps(view)
    def authenticated_view(*args, **kwargs):
        authorization_header = request.headers.get(constants.AUTHORIZATION_HEADER)
        expected_token = current_app.config[constants.CONFIG_STATIC_BEARER_TOKEN]
        if not is_valid_bearer_token(authorization_header, expected_token):
            return {constants.KEY_MESSAGE: constants.MESSAGE_UNAUTHORIZED}, HTTPStatus.UNAUTHORIZED
        return view(*args, **kwargs)

    return authenticated_view
