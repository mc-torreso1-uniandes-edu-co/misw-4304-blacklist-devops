import os

from dotenv import load_dotenv

from app import constants

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get(constants.ENV_DATABASE_URL)
    JWT_SECRET_KEY = os.environ.get(constants.ENV_JWT_SECRET_KEY)
    PROPAGATE_EXCEPTIONS = True


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(constants.ENV_DATABASE_URL, constants.TEST_DATABASE_URI)
    JWT_SECRET_KEY = constants.TEST_JWT_SECRET_KEY


CONFIG_BY_ENVIRONMENT = {
    constants.APP_ENV_DEVELOPMENT: Config,
    constants.APP_ENV_PRODUCTION: Config,
    constants.APP_ENV_TESTING: TestConfig,
}


def resolve_config_class():
    environment = os.environ.get(constants.ENV_APP_ENV, "").strip().lower() or constants.DEFAULT_APP_ENV
    try:
        return CONFIG_BY_ENVIRONMENT[environment]
    except KeyError:
        valid_environments = ", ".join(sorted(CONFIG_BY_ENVIRONMENT))
        raise ValueError(
            constants.ERROR_INVALID_APP_ENV.format(value=environment, valid=valid_environments)
        ) from None
