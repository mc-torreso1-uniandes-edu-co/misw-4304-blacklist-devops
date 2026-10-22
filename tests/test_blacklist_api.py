from datetime import timezone
from http import HTTPStatus
from uuid import uuid4

from flask_jwt_extended import create_access_token
from sqlalchemy import select

from app import constants, create_app
from app.config import TestConfig
from app.domain.clock import utc_now
from app.extensions import db
from app.infrastructure.persistence.blacklist_entry_model import BlacklistEntryModel
from app.infrastructure.persistence.sqlalchemy_blacklist_repository import SqlAlchemyBlacklistRepository
from tests.conftest import bearer_headers

SAMPLE_REASON = "Fraude comprobado"
INVALID_EMAIL = "no-es-un-email"
INVALID_UUID = "no-es-un-uuid"
CLIENT_IP = "203.0.113.7"
PROXY_IP = "172.31.10.20"
FORWARDED_FOR_HEADER = "X-Forwarded-For"
FORWARDED_FOR_CHAIN = f"{CLIENT_IP}, {PROXY_IP}"


def blacklist_path(email):
    return f"{constants.BLACKLISTS_PATH}/{email}"


def valid_payload(email, **overrides):
    payload = {
        constants.FIELD_EMAIL: email,
        constants.FIELD_APP_UUID: str(uuid4()),
        constants.FIELD_BLOCKED_REASON: SAMPLE_REASON,
    }
    payload.update(overrides)
    return payload


def test_post_adds_email_and_returns_id(client, auth_headers, unique_email):
    response = client.post(constants.BLACKLISTS_PATH, json=valid_payload(unique_email), headers=auth_headers)

    body = response.get_json()
    assert response.status_code == HTTPStatus.CREATED
    assert body[constants.KEY_MSG] == constants.MESSAGE_EMAIL_ADDED
    assert isinstance(body[constants.KEY_ID], int)


def test_post_without_blocked_reason_is_allowed(client, auth_headers, unique_email):
    payload = valid_payload(unique_email)
    del payload[constants.FIELD_BLOCKED_REASON]

    response = client.post(constants.BLACKLISTS_PATH, json=payload, headers=auth_headers)

    assert response.status_code == HTTPStatus.CREATED


def test_post_with_null_blocked_reason_is_allowed(client, auth_headers, unique_email):
    payload = valid_payload(unique_email, **{constants.FIELD_BLOCKED_REASON: None})

    response = client.post(constants.BLACKLISTS_PATH, json=payload, headers=auth_headers)

    assert response.status_code == HTTPStatus.CREATED


def test_post_stores_creation_date(app, client, auth_headers, unique_email):
    before = utc_now()

    client.post(constants.BLACKLISTS_PATH, json=valid_payload(unique_email), headers=auth_headers)

    after = utc_now()
    with app.app_context():
        stored = db.session.execute(select(BlacklistEntryModel).filter_by(email=unique_email)).scalar_one()
    created_at = stored.created_at
    created_at_utc = created_at.replace(tzinfo=timezone.utc) if created_at.tzinfo is None else created_at
    assert before <= created_at_utc <= after


def test_post_duplicated_email_returns_conflict(client, auth_headers, unique_email):
    client.post(constants.BLACKLISTS_PATH, json=valid_payload(unique_email), headers=auth_headers)

    response = client.post(constants.BLACKLISTS_PATH, json=valid_payload(unique_email), headers=auth_headers)

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.get_json()[constants.KEY_MSG] == constants.MESSAGE_EMAIL_ALREADY_BLACKLISTED


def test_post_duplicated_email_with_different_case_returns_conflict(client, auth_headers, unique_email):
    client.post(constants.BLACKLISTS_PATH, json=valid_payload(unique_email), headers=auth_headers)

    response = client.post(
        constants.BLACKLISTS_PATH, json=valid_payload(unique_email.upper()), headers=auth_headers
    )

    assert response.status_code == HTTPStatus.CONFLICT


def test_post_duplicated_email_with_surrounding_spaces_returns_conflict(client, auth_headers, unique_email):
    client.post(constants.BLACKLISTS_PATH, json=valid_payload(unique_email), headers=auth_headers)

    response = client.post(
        constants.BLACKLISTS_PATH, json=valid_payload(f"  {unique_email}  "), headers=auth_headers
    )

    assert response.status_code == HTTPStatus.CONFLICT


def test_post_stores_email_normalized(app, client, auth_headers, unique_email):
    client.post(constants.BLACKLISTS_PATH, json=valid_payload(unique_email.upper()), headers=auth_headers)

    with app.app_context():
        stored = db.session.execute(select(BlacklistEntryModel).filter_by(email=unique_email)).scalar_one()

    assert stored.email == unique_email


def test_post_returns_conflict_when_concurrent_request_wins_the_race(
    client, auth_headers, unique_email, monkeypatch
):
    client.post(constants.BLACKLISTS_PATH, json=valid_payload(unique_email), headers=auth_headers)
    monkeypatch.setattr(SqlAlchemyBlacklistRepository, "find_by_email", lambda self, email: None)

    response = client.post(constants.BLACKLISTS_PATH, json=valid_payload(unique_email), headers=auth_headers)

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.get_json()[constants.KEY_MSG] == constants.MESSAGE_EMAIL_ALREADY_BLACKLISTED


def test_post_stores_ip_from_forwarded_for_header(app, client, auth_headers, unique_email):
    headers = {**auth_headers, FORWARDED_FOR_HEADER: CLIENT_IP}

    client.post(constants.BLACKLISTS_PATH, json=valid_payload(unique_email), headers=headers)

    with app.app_context():
        stored = db.session.execute(select(BlacklistEntryModel).filter_by(email=unique_email)).scalar_one()
    assert stored.ip_address == CLIENT_IP


def stored_ip_for_forwarded_chain(application, forwarded_for):
    email = f"{uuid4().hex}@example.com"
    with application.app_context():
        token = create_access_token(identity=constants.TOKEN_IDENTITY, expires_delta=False)
    headers = {**bearer_headers(token), FORWARDED_FOR_HEADER: forwarded_for}

    application.test_client().post(constants.BLACKLISTS_PATH, json=valid_payload(email), headers=headers)

    with application.app_context():
        stored = db.session.execute(select(BlacklistEntryModel).filter_by(email=email)).scalar_one()
        ip_address = stored.ip_address
        db.session.remove()
        db.engine.dispose()
    return ip_address


def test_post_with_one_trusted_hop_stores_last_proxy_of_chain(app):
    assert stored_ip_for_forwarded_chain(app, FORWARDED_FOR_CHAIN) == PROXY_IP


def test_post_with_two_trusted_hops_stores_client_ip_of_chain():
    class TwoHopsConfig(TestConfig):
        PROXY_FIX_X_FOR = 2

    assert stored_ip_for_forwarded_chain(create_app(TwoHopsConfig), FORWARDED_FOR_CHAIN) == CLIENT_IP


def test_post_rejects_invalid_email(client, auth_headers):
    response = client.post(
        constants.BLACKLISTS_PATH, json=valid_payload(INVALID_EMAIL), headers=auth_headers
    )

    body = response.get_json()
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert body[constants.KEY_MSG] == constants.MESSAGE_INVALID_REQUEST
    assert constants.FIELD_EMAIL in body[constants.KEY_ERRORS]


def test_post_rejects_invalid_app_uuid(client, auth_headers, unique_email):
    payload = valid_payload(unique_email, **{constants.FIELD_APP_UUID: INVALID_UUID})

    response = client.post(constants.BLACKLISTS_PATH, json=payload, headers=auth_headers)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert constants.FIELD_APP_UUID in response.get_json()[constants.KEY_ERRORS]


def test_post_rejects_too_long_blocked_reason(client, auth_headers, unique_email):
    too_long_reason = "a" * (constants.BLOCKED_REASON_MAX_LENGTH + 1)
    payload = valid_payload(unique_email, **{constants.FIELD_BLOCKED_REASON: too_long_reason})

    response = client.post(constants.BLACKLISTS_PATH, json=payload, headers=auth_headers)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert constants.FIELD_BLOCKED_REASON in response.get_json()[constants.KEY_ERRORS]


def test_post_accepts_blocked_reason_at_max_length(client, auth_headers, unique_email):
    max_length_reason = "a" * constants.BLOCKED_REASON_MAX_LENGTH
    payload = valid_payload(unique_email, **{constants.FIELD_BLOCKED_REASON: max_length_reason})

    response = client.post(constants.BLACKLISTS_PATH, json=payload, headers=auth_headers)

    assert response.status_code == HTTPStatus.CREATED


def test_post_rejects_missing_required_fields(client, auth_headers):
    response = client.post(constants.BLACKLISTS_PATH, json={}, headers=auth_headers)

    body = response.get_json()
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert constants.FIELD_EMAIL in body[constants.KEY_ERRORS]
    assert constants.FIELD_APP_UUID in body[constants.KEY_ERRORS]


def test_post_rejects_body_that_is_not_json(client, auth_headers):
    response = client.post(
        constants.BLACKLISTS_PATH, data="esto no es json", content_type="text/plain", headers=auth_headers
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_rejects_malformed_json_body(client, auth_headers):
    response = client.post(
        constants.BLACKLISTS_PATH, data="{no cierra", content_type="application/json", headers=auth_headers
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_returns_true_and_reason_for_blacklisted_email(client, auth_headers, unique_email):
    client.post(constants.BLACKLISTS_PATH, json=valid_payload(unique_email), headers=auth_headers)

    response = client.get(blacklist_path(unique_email), headers=auth_headers)

    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {
        constants.KEY_IS_BLACKLISTED: True,
        constants.FIELD_BLOCKED_REASON: SAMPLE_REASON,
    }


def test_get_is_case_insensitive(client, auth_headers, unique_email):
    client.post(constants.BLACKLISTS_PATH, json=valid_payload(unique_email), headers=auth_headers)

    response = client.get(blacklist_path(unique_email.upper()), headers=auth_headers)

    assert response.get_json()[constants.KEY_IS_BLACKLISTED] is True


def test_get_returns_false_for_unknown_email(client, auth_headers, unique_email):
    response = client.get(blacklist_path(unique_email), headers=auth_headers)

    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {
        constants.KEY_IS_BLACKLISTED: False,
        constants.FIELD_BLOCKED_REASON: None,
    }
