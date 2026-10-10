from http import HTTPStatus
from uuid import uuid4

from app import constants

SAMPLE_EMAIL = "cliente@example.com"
SAMPLE_REASON = "Fraude comprobado"
UNKNOWN_EMAIL = "otro@example.com"
INVALID_EMAIL = "no-es-un-email"
INVALID_UUID = "no-es-un-uuid"
WRONG_TOKEN_HEADERS = {constants.AUTHORIZATION_HEADER: f"{constants.BEARER_PREFIX}token-incorrecto"}


def valid_payload(**overrides):
    payload = {
        constants.FIELD_EMAIL: SAMPLE_EMAIL,
        constants.FIELD_APP_UUID: str(uuid4()),
        constants.FIELD_BLOCKED_REASON: SAMPLE_REASON,
    }
    payload.update(overrides)
    return payload


def test_post_adds_email(client, auth_headers):
    response = client.post(constants.BLACKLISTS_PATH, json=valid_payload(), headers=auth_headers)

    assert response.status_code == HTTPStatus.CREATED
    assert response.get_json()[constants.KEY_MESSAGE] == constants.MESSAGE_EMAIL_ADDED


def test_post_without_blocked_reason_is_allowed(client, auth_headers):
    payload = valid_payload()
    del payload[constants.FIELD_BLOCKED_REASON]

    response = client.post(constants.BLACKLISTS_PATH, json=payload, headers=auth_headers)

    assert response.status_code == HTTPStatus.CREATED


def test_post_duplicated_email_returns_conflict(client, auth_headers):
    client.post(constants.BLACKLISTS_PATH, json=valid_payload(), headers=auth_headers)

    response = client.post(constants.BLACKLISTS_PATH, json=valid_payload(), headers=auth_headers)

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.get_json()[constants.KEY_MESSAGE] == constants.MESSAGE_EMAIL_ALREADY_BLACKLISTED


def test_post_rejects_invalid_email(client, auth_headers):
    payload = valid_payload(**{constants.FIELD_EMAIL: INVALID_EMAIL})

    response = client.post(constants.BLACKLISTS_PATH, json=payload, headers=auth_headers)

    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_rejects_invalid_app_uuid(client, auth_headers):
    payload = valid_payload(**{constants.FIELD_APP_UUID: INVALID_UUID})

    response = client.post(constants.BLACKLISTS_PATH, json=payload, headers=auth_headers)

    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_rejects_too_long_blocked_reason(client, auth_headers):
    too_long_reason = "a" * (constants.BLOCKED_REASON_MAX_LENGTH + 1)
    payload = valid_payload(**{constants.FIELD_BLOCKED_REASON: too_long_reason})

    response = client.post(constants.BLACKLISTS_PATH, json=payload, headers=auth_headers)

    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_rejects_missing_required_fields(client, auth_headers):
    response = client.post(constants.BLACKLISTS_PATH, json={}, headers=auth_headers)

    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_post_without_token_is_unauthorized(client):
    response = client.post(constants.BLACKLISTS_PATH, json=valid_payload())

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_post_with_wrong_token_is_unauthorized(client):
    response = client.post(constants.BLACKLISTS_PATH, json=valid_payload(), headers=WRONG_TOKEN_HEADERS)

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_returns_true_and_reason_for_blacklisted_email(client, auth_headers):
    client.post(constants.BLACKLISTS_PATH, json=valid_payload(), headers=auth_headers)

    response = client.get(f"{constants.BLACKLISTS_PATH}/{SAMPLE_EMAIL}", headers=auth_headers)

    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {
        constants.KEY_IS_BLACKLISTED: True,
        constants.FIELD_BLOCKED_REASON: SAMPLE_REASON,
    }


def test_get_returns_false_for_unknown_email(client, auth_headers):
    response = client.get(f"{constants.BLACKLISTS_PATH}/{UNKNOWN_EMAIL}", headers=auth_headers)

    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {
        constants.KEY_IS_BLACKLISTED: False,
        constants.FIELD_BLOCKED_REASON: None,
    }


def test_get_without_token_is_unauthorized(client):
    response = client.get(f"{constants.BLACKLISTS_PATH}/{SAMPLE_EMAIL}")

    assert response.status_code == HTTPStatus.UNAUTHORIZED
