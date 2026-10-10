from flask_restful import Resource

from app.application.use_cases.add_email_to_blacklist import AddEmailToBlacklist
from app.application.use_cases.check_email_in_blacklist import CheckEmailInBlacklist


class BlacklistResource(Resource):
    def __init__(self, add_email_to_blacklist: AddEmailToBlacklist):
        self._add_email_to_blacklist = add_email_to_blacklist

    def post(self):
        raise NotImplementedError


class BlacklistEmailResource(Resource):
    def __init__(self, check_email_in_blacklist: CheckEmailInBlacklist):
        self._check_email_in_blacklist = check_email_in_blacklist

    def get(self, email: str):
        raise NotImplementedError
