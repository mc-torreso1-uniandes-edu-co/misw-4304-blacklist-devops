import os

from dotenv import load_dotenv

from app import constants

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get(constants.ENV_DATABASE_URL)
    STATIC_BEARER_TOKEN = os.environ.get(constants.ENV_STATIC_BEARER_TOKEN)
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = constants.TEST_DATABASE_URI
    STATIC_BEARER_TOKEN = constants.TEST_STATIC_BEARER_TOKEN
