from uuid import uuid4

import pytest
from flask_jwt_extended import create_access_token

from app import constants, create_app
from app.config import TestConfig
from app.extensions import db

AUTHORIZATION_HEADER = "Authorization"
BEARER_PREFIX = "Bearer "


def bearer_headers(token):
    return {AUTHORIZATION_HEADER: f"{BEARER_PREFIX}{token}"}


@pytest.fixture
def app():
    application = create_app(TestConfig)
    yield application
    with application.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(app):
    with app.app_context():
        token = create_access_token(identity=constants.TOKEN_IDENTITY, expires_delta=False)
    return bearer_headers(token)


@pytest.fixture
def unique_email():
    return f"{uuid4().hex}@example.com"
