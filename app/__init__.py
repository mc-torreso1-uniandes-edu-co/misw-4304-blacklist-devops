from flask import Flask

from app.application.use_cases.add_email_to_blacklist import AddEmailToBlacklist
from app.application.use_cases.check_email_in_blacklist import CheckEmailInBlacklist
from app.config import Config
from app.extensions import db, jwt, ma
from app.infrastructure.http.routes import register_routes
from app.infrastructure.persistence import blacklist_entry_model
from app.infrastructure.persistence.sqlalchemy_blacklist_repository import SqlAlchemyBlacklistRepository


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)

    repository = SqlAlchemyBlacklistRepository(db.session)
    register_routes(
        app,
        add_email_to_blacklist=AddEmailToBlacklist(repository),
        check_email_in_blacklist=CheckEmailInBlacklist(repository),
    )
    return app
