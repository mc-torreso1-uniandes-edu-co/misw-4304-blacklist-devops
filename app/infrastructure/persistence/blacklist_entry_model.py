from app import constants
from app.extensions import db


class BlacklistEntryModel(db.Model):
    __tablename__ = constants.BLACKLIST_TABLE_NAME

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(constants.EMAIL_MAX_LENGTH), nullable=False, index=True)
    app_uuid = db.Column(db.String(constants.UUID_STRING_LENGTH), nullable=False)
    blocked_reason = db.Column(db.String(constants.BLOCKED_REASON_MAX_LENGTH), nullable=True)
    request_ip = db.Column(db.String(constants.IP_ADDRESS_MAX_LENGTH), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
