from pathlib import Path

from flask import Flask
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.middleware.proxy_fix import ProxyFix

from app import constants
from app.application.use_cases.add_email_to_blacklist import AddEmailToBlacklist
from app.application.use_cases.check_email_in_blacklist import CheckEmailInBlacklist
from app.config import read_forwarded_for_hops, resolve_config_class
from app.extensions import db, jwt, ma
from app.infrastructure.http.authentication import register_jwt_error_handlers
from app.infrastructure.http.routes import register_routes
from app.infrastructure.persistence import blacklist_entry_model
from app.infrastructure.persistence.sqlalchemy_blacklist_repository import SqlAlchemyBlacklistRepository
from app.version import read_app_version


def create_tables(app: Flask) -> None:
    with app.app_context():
        try:
            db.create_all()
        except SQLAlchemyError:
            app.logger.exception(constants.LOG_CREATE_TABLES_FAILED)


def create_app(config_class=None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class or resolve_config_class())
    app.config[constants.CONFIG_APP_VERSION] = read_app_version(
        Path(app.root_path).parent / constants.VERSION_FILE_NAME
    )
    forwarded_for_hops = app.config.get(constants.CONFIG_PROXY_FIX_X_FOR) or read_forwarded_for_hops()
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=forwarded_for_hops)

    db.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)
    register_jwt_error_handlers(jwt)
    create_tables(app)

    repository = SqlAlchemyBlacklistRepository(db.session)
    register_routes(
        app,
        add_email_to_blacklist=AddEmailToBlacklist(repository),
        check_email_in_blacklist=CheckEmailInBlacklist(repository),
    )
    return app
