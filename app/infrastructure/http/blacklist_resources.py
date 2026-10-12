from http import HTTPStatus

from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from marshmallow import ValidationError

from app import constants
from app.application.use_cases.add_email_to_blacklist import AddEmailToBlacklist
from app.application.use_cases.check_email_in_blacklist import CheckEmailInBlacklist
from app.domain.clock import utc_now
from app.domain.errors import EmailAlreadyBlacklistedError
from app.infrastructure.http.blacklist_entry_schema import AddBlacklistEntryRequestSchema


class BlacklistResource(Resource):
    method_decorators = [jwt_required()]

    def __init__(self, add_email_to_blacklist: AddEmailToBlacklist):
        self._add_email_to_blacklist = add_email_to_blacklist
        self._request_schema = AddBlacklistEntryRequestSchema()

    def post(self):
        try:
            payload = self._request_schema.load(request.get_json(silent=True) or {})
        except ValidationError as validation_error:
            return {
                constants.KEY_MSG: constants.MESSAGE_INVALID_REQUEST,
                constants.KEY_ERRORS: validation_error.messages,
            }, HTTPStatus.BAD_REQUEST
        try:
            entry = self._add_email_to_blacklist.execute(
                email=payload[constants.FIELD_EMAIL],
                app_uuid=payload[constants.FIELD_APP_UUID],
                blocked_reason=payload[constants.FIELD_BLOCKED_REASON],
                ip_address=request.remote_addr,
                requested_at=utc_now(),
            )
        except EmailAlreadyBlacklistedError:
            return {constants.KEY_MSG: constants.MESSAGE_EMAIL_ALREADY_BLACKLISTED}, HTTPStatus.CONFLICT
        return {constants.KEY_MSG: constants.MESSAGE_EMAIL_ADDED, constants.KEY_ID: entry.id}, HTTPStatus.CREATED


class BlacklistEmailResource(Resource):
    method_decorators = [jwt_required()]

    def __init__(self, check_email_in_blacklist: CheckEmailInBlacklist):
        self._check_email_in_blacklist = check_email_in_blacklist

    def get(self, email: str):
        entry = self._check_email_in_blacklist.execute(email)
        return {
            constants.KEY_IS_BLACKLISTED: entry is not None,
            constants.FIELD_BLOCKED_REASON: None if entry is None else entry.blocked_reason,
        }, HTTPStatus.OK
