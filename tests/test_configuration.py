import logging

from sqlalchemy.exc import OperationalError

from app import constants, create_app, create_tables
from app.config import Config, TestConfig, resolve_config_class
from app.extensions import db


def test_resolve_config_class_uses_testing_environment(monkeypatch):
    monkeypatch.setenv(constants.ENV_APP_ENV, constants.APP_ENV_TESTING)

    assert resolve_config_class() is TestConfig


def test_resolve_config_class_defaults_to_development(monkeypatch):
    monkeypatch.delenv(constants.ENV_APP_ENV, raising=False)

    assert resolve_config_class() is Config


def test_create_tables_logs_error_instead_of_failing(app, monkeypatch, caplog):
    def fail_to_create_tables():
        raise OperationalError("create_all", {}, Exception())

    monkeypatch.setattr(db, "create_all", fail_to_create_tables)

    with caplog.at_level(logging.ERROR):
        create_tables(app)

    assert constants.LOG_CREATE_TABLES_FAILED in caplog.text


def test_create_app_without_explicit_config_uses_environment(monkeypatch):
    monkeypatch.setenv(constants.ENV_APP_ENV, constants.APP_ENV_TESTING)

    application = create_app()

    assert application.config["TESTING"] is True
