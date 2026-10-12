from http import HTTPStatus

from app import constants
from app.version import read_app_version


def test_ping_does_not_require_token(client):
    response = client.get(constants.PING_PATH)

    assert response.status_code == HTTPStatus.OK


def test_ping_returns_only_the_version(client, app):
    response = client.get(constants.PING_PATH)

    assert response.get_json() == {constants.KEY_VERSION: app.config[constants.CONFIG_APP_VERSION]}


def test_read_app_version_returns_file_content(tmp_path):
    version_file = tmp_path / constants.VERSION_FILE_NAME
    version_file.write_text("v7\n", encoding="utf-8")

    assert read_app_version(version_file) == "v7"


def test_read_app_version_returns_default_when_file_is_missing(tmp_path):
    assert read_app_version(tmp_path / constants.VERSION_FILE_NAME) == constants.DEFAULT_APP_VERSION


def test_read_app_version_returns_default_when_file_is_empty(tmp_path):
    version_file = tmp_path / constants.VERSION_FILE_NAME
    version_file.write_text("  \n", encoding="utf-8")

    assert read_app_version(version_file) == constants.DEFAULT_APP_VERSION
