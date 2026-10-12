import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from app import constants
from app.config import Config


def generate_static_token() -> str:
    app = Flask(__name__)
    app.config.from_object(Config)
    JWTManager(app)
    with app.app_context():
        return create_access_token(identity=constants.TOKEN_IDENTITY, expires_delta=False)


if __name__ == "__main__":
    print(generate_static_token())
