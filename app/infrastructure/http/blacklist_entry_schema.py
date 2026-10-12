from marshmallow import Schema, fields, pre_load, validate

from app import constants
from app.domain.email import normalize_email


class AddBlacklistEntryRequestSchema(Schema):
    email = fields.Email(required=True, validate=validate.Length(max=constants.EMAIL_MAX_LENGTH))
    app_uuid = fields.UUID(required=True)
    blocked_reason = fields.String(
        required=False,
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=constants.BLOCKED_REASON_MAX_LENGTH),
    )

    @pre_load
    def normalize_email_field(self, data, **kwargs):
        email = data.get(constants.FIELD_EMAIL) if isinstance(data, dict) else None
        if isinstance(email, str):
            return {**data, constants.FIELD_EMAIL: normalize_email(email)}
        return data
