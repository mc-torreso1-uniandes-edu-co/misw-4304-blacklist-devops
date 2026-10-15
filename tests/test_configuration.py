import logging

import pytest
from sqlalchemy.exc import OperationalError

from app import constants, create_app, create_tables
from app.config import Config, TestConfig, read_forwarded_for_hops, resolve_config_class
from app.extensions import db


def test_resolve_config_class_uses_testing_environment(monkeypatch):
    monkeypatch.setenv(constants.ENV_APP_ENV, constants.APP_ENV_TESTING)

    assert resolve_config_class() is TestConfig


def test_resolve_config_class_defaults_to_development(monkeypatch):
    monkeypatch.delenv(constants.ENV_APP_ENV, raising=False)

    assert resolve_config_class() is Config


@pytest.mark.parametrize("value", ["", "   "])
def test_resolve_config_class_treats_empty_value_as_default(monkeypatch, value):
    monkeypatch.setenv(constants.ENV_APP_ENV, value)

    assert resolve_config_class() is Config


def test_resolve_config_class_ignores_case_and_spaces(monkeypatch):
    monkeypatch.setenv(constants.ENV_APP_ENV, "  Testing ")

    assert resolve_config_class() is TestConfig


def test_resolve_config_class_rejects_unknown_value(monkeypatch):
    monkeypatch.setenv(constants.ENV_APP_ENV, "staging")

    with pytest.raises(ValueError, match="staging") as error:
        resolve_config_class()

    for environment in (constants.APP_ENV_DEVELOPMENT, constants.APP_ENV_PRODUCTION, constants.APP_ENV_TESTING):
        assert environment in str(error.value)


@pytest.mark.parametrize("value", [None, "", "  "])
def test_read_forwarded_for_hops_defaults_to_one(monkeypatch, value):
    if value is None:
        monkeypatch.delenv(constants.ENV_PROXY_FIX_X_FOR, raising=False)
    else:
        monkeypatch.setenv(constants.ENV_PROXY_FIX_X_FOR, value)

    assert read_forwarded_for_hops() == constants.DEFAULT_PROXY_FORWARDED_FOR_HOPS


def test_read_forwarded_for_hops_uses_environment_value(monkeypatch):
    monkeypatch.setenv(constants.ENV_PROXY_FIX_X_FOR, " 2 ")

    assert read_forwarded_for_hops() == 2


@pytest.mark.parametrize("value", ["0", "-1", "dos", "1.5"])
def test_read_forwarded_for_hops_rejects_invalid_value(monkeypatch, value):
    monkeypatch.setenv(constants.ENV_PROXY_FIX_X_FOR, value)

    with pytest.raises(ValueError, match=constants.ENV_PROXY_FIX_X_FOR):
        read_forwarded_for_hops()


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
    with application.app_context():
        db.session.remove()
        db.engine.dispose()
