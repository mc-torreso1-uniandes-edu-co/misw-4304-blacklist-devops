from http import HTTPStatus
from uuid import uuid4

import pytest
from flask_jwt_extended import create_access_token

from app import constants
from tests.conftest import AUTHORIZATION_HEADER, bearer_headers

OTHER_SECRET_KEY = "otra-clave-secreta-distinta-con-longitud-suficiente"
MALFORMED_TOKEN = "esto.no.es-un-jwt"
UNSUPPORTED_SCHEME_HEADER = {AUTHORIZATION_HEADER: "Basic dXN1YXJpbzpjbGF2ZQ=="}
BEARER_WITHOUT_TOKEN_HEADER = {AUTHORIZATION_HEADER: "Bearer"}
REJECTED_SCENARIOS = (
    "sin token",
    "token malformado",
    "esquema no soportado",
    "bearer sin token",
    "firma con otra clave",
)


def post_payload(email):
    return {constants.FIELD_EMAIL: email, constants.FIELD_APP_UUID: str(uuid4())}


def token_signed_with_other_secret(app):
    app.config[constants.CONFIG_JWT_SECRET_KEY] = OTHER_SECRET_KEY
    with app.app_context():
        token = create_access_token(identity=constants.TOKEN_IDENTITY)
    app.config[constants.CONFIG_JWT_SECRET_KEY] = constants.TEST_JWT_SECRET_KEY
    return token


def rejected_headers(app):
    return {
        "sin token": {},
        "token malformado": bearer_headers(MALFORMED_TOKEN),
        "esquema no soportado": UNSUPPORTED_SCHEME_HEADER,
        "bearer sin token": BEARER_WITHOUT_TOKEN_HEADER,
        "firma con otra clave": bearer_headers(token_signed_with_other_secret(app)),
    }


@pytest.mark.parametrize("scenario", REJECTED_SCENARIOS)
def test_post_rejects_invalid_credentials_with_unauthorized(app, client, unique_email, scenario):
    headers = rejected_headers(app)[scenario]

    response = client.post(constants.BLACKLISTS_PATH, json=post_payload(unique_email), headers=headers)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert constants.KEY_MSG in response.get_json()


def test_get_rejects_invalid_credentials_with_unauthorized(app, client, unique_email):
    for scenario, headers in rejected_headers(app).items():
        response = client.get(f"{constants.BLACKLISTS_PATH}/{unique_email}", headers=headers)

        assert response.status_code == HTTPStatus.UNAUTHORIZED, scenario
        assert constants.KEY_MSG in response.get_json(), scenario
