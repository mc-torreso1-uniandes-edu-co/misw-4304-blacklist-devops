import pytest

from app import constants, create_app
from app.config import TestConfig


@pytest.fixture
def app():
    return create_app(TestConfig)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers():
    return {constants.AUTHORIZATION_HEADER: f"{constants.BEARER_PREFIX}{constants.TEST_STATIC_BEARER_TOKEN}"}
