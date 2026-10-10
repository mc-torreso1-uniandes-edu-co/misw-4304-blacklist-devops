from marshmallow import Schema, fields, validate

from app import constants


class AddBlacklistEntryRequestSchema(Schema):
    email = fields.Email(required=True, validate=validate.Length(max=constants.EMAIL_MAX_LENGTH))
    app_uuid = fields.UUID(required=True)
    blocked_reason = fields.String(
        required=False,
        load_default=None,
        validate=validate.Length(max=constants.BLOCKED_REASON_MAX_LENGTH),
    )
