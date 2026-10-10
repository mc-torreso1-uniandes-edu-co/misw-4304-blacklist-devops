from flask import Flask
from flask_restful import Api

from app import constants
from app.application.use_cases.add_email_to_blacklist import AddEmailToBlacklist
from app.application.use_cases.check_email_in_blacklist import CheckEmailInBlacklist
from app.infrastructure.http.blacklist_resources import BlacklistEmailResource, BlacklistResource

ADD_USE_CASE_KWARG = "add_email_to_blacklist"
CHECK_USE_CASE_KWARG = "check_email_in_blacklist"


def register_routes(
    app: Flask,
    add_email_to_blacklist: AddEmailToBlacklist,
    check_email_in_blacklist: CheckEmailInBlacklist,
) -> None:
    api = Api(app)
    api.add_resource(
        BlacklistResource,
        constants.BLACKLISTS_PATH,
        resource_class_kwargs={ADD_USE_CASE_KWARG: add_email_to_blacklist},
    )
    api.add_resource(
        BlacklistEmailResource,
        constants.BLACKLIST_EMAIL_PATH,
        resource_class_kwargs={CHECK_USE_CASE_KWARG: check_email_in_blacklist},
    )
