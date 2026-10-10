from http import HTTPStatus

from app import constants


def test_ping_does_not_require_token(client):
    response = client.get(constants.PING_PATH)

    assert response.status_code == HTTPStatus.OK


def test_ping_returns_configured_version(client, app):
    response = client.get(constants.PING_PATH)

    assert response.get_json() == {constants.KEY_VERSION: app.config[constants.CONFIG_APP_VERSION]}
