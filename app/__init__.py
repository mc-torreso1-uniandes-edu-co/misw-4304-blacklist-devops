from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app import constants
from app.application.use_cases.add_email_to_blacklist import AddEmailToBlacklist
from app.application.use_cases.check_email_in_blacklist import CheckEmailInBlacklist
from app.config import Config
from app.extensions import db, ma
from app.infrastructure.http.routes import register_routes
from app.infrastructure.persistence import blacklist_entry_model
from app.infrastructure.persistence.sqlalchemy_blacklist_repository import SqlAlchemyBlacklistRepository


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=constants.PROXY_FORWARDED_FOR_HOPS)

    db.init_app(app)
    ma.init_app(app)
    with app.app_context():
        db.create_all()

    repository = SqlAlchemyBlacklistRepository(db.session)
    register_routes(
        app,
        add_email_to_blacklist=AddEmailToBlacklist(repository),
        check_email_in_blacklist=CheckEmailInBlacklist(repository),
    )
    return app
